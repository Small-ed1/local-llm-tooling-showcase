from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import base64
import json
import os
import subprocess

import pytest

from tooling_showcase.config import OllamaConfig, ShellPolicy, ShowcaseConfig
from tooling_showcase.models import ToolCall
from tooling_showcase.tools import ToolRuntime


def make_runtime(
    tmp_path: Path, *, project_equals_workspace: bool = False
) -> ToolRuntime:
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    project_root = workspace if project_equals_workspace else tmp_path
    config = ShowcaseConfig(
        project_root=project_root,
        workspace_root=workspace,
        portfolio_root=tmp_path,
        journal_path=tmp_path / "state" / "events.jsonl",
        ollama=OllamaConfig(enabled=False, model="llama3.1:latest"),
        shell_policy=ShellPolicy(timeout_seconds=10),
    )
    return ToolRuntime(config)


def test_runtime_exposes_requested_tool_surface(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    expected = {
        "file_search",
        "read_file",
        "write_file",
        "create_file",
        "append_file",
        "apply_patch",
        "delete_file",
        "move_file",
        "copy_file",
        "list_directory",
        "get_file_info",
        "tree_view",
        "grep_search",
        "find_symbol",
        "run_tests",
        "lint_code",
        "format_code",
        "execute_script",
        "build_project",
        "install_dependencies",
        "git_status",
        "git_diff",
        "git_log",
        "git_add",
        "git_commit",
        "git_checkout",
        "git_branch",
        "git_merge",
        "git_reset",
        "git_stash",
        "shell_command",
        "safe_shell_command",
        "process_list",
        "kill_process",
        "system_info",
        "env_vars",
        "web_search",
        "fetch_url",
        "extract_webpage_content",
        "download_file",
        "parse_pdf",
        "parse_json_api",
        "screenshot_page",
        "local_doc_paths",
        "local_doc_search",
        "local_doc_read",
        "local_doc_replace",
        "tool_structure",
        "build_index",
        "query_index",
        "update_index",
        "delete_from_index",
        "list_indexed_sources",
        "save_memory",
        "load_memory",
        "update_memory",
        "delete_memory",
        "list_memories",
        "task_checkpoint",
        "load_checkpoint",
        "summarize_session",
        "plan_task",
        "execute_step",
        "mark_step_complete",
        "retry_step",
        "abort_task",
        "get_task_status",
        "request_user_approval",
        "check_permission",
        "log_sensitive_action",
        "sandbox_file_access",
        "sandbox_shell_execution",
        "log_event",
        "trace_step",
        "record_tool_latency",
        "record_error",
        "replay_session",
        "summarize_run",
        "calculate",
        "datetime_now",
        "convert_units",
        "generate_uuid",
        "hash_file",
        "encode_decode",
        "create_memory",
        "edit_memory",
        "run_model",
        "transcribe_audio",
        "text_to_speech",
        "analyze_image",
        "control_device",
        "adapter_inventory",
    }
    assert expected <= set(runtime.available_tools())
    assert runtime.aliases["search_text"] == "grep_search"
    assert runtime.aliases["patch_file"] == "apply_patch"
    assert runtime.aliases["rename_file"] == "move_file"

    structure = runtime.tool_structure()
    assert structure.ok is True
    assert "local_doc_search" in structure.data["planner_visible"]
    assert "local_doc_replace" in structure.data["manual_only"]
    assert structure.data["aliases"]["search_text"] == "grep_search"


def test_filesystem_and_utility_tools(tmp_path: Path):
    runtime = make_runtime(tmp_path)

    assert runtime.create_file("notes.txt", "alpha").ok is True
    assert runtime.append_file("notes.txt", "\nbeta").ok is True
    assert runtime.read_file("notes.txt").summary == "alpha\nbeta"
    assert runtime.write_file("notes.txt", "gamma\ndelta").ok is True
    assert runtime.apply_patch("notes.txt", "delta", "omega").ok is True
    assert runtime.copy_file("notes.txt", "copy.txt").ok is True
    assert runtime.move_file("copy.txt", "moved.txt").ok is True

    listing = runtime.list_directory()
    assert listing.ok is True
    assert "moved.txt" in listing.summary

    tree = runtime.tree_view()
    assert tree.ok is True
    assert "notes.txt" in tree.summary

    info = runtime.get_file_info("notes.txt")
    assert info.ok is True
    assert info.data["size"] > 0

    digest = runtime.hash_file("notes.txt")
    assert digest.ok is True
    assert len(digest.summary) == 64

    assert runtime.encode_decode("encode", "hello").ok is True
    assert runtime.encode_decode("decode", "aGVsbG8=").summary == "hello"
    assert runtime.calculate("(2 + 3) * 4").summary == "20.0"
    assert runtime.convert_units(2, "km", "m").summary == "2000.0"
    assert runtime.datetime_now().ok is True
    assert runtime.generate_uuid().ok is True

    assert runtime.delete_file("moved.txt").ok is True
    assert runtime.sandbox_file_access("../escape.txt").ok is False


def test_local_documentation_lookup_and_edits_are_scoped(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    docs_dir = runtime.config.workspace_root / "docs"
    docs_dir.mkdir()
    (runtime.config.workspace_root / "README.md").write_text("# Demo\n\nRelease checks live here.\n", encoding="utf-8")
    (docs_dir / "TOOLS.md").write_text("# Tools\n\nOld docs line.\n", encoding="utf-8")
    (runtime.config.workspace_root / "src.py").write_text("Old docs line.\n", encoding="utf-8")

    paths = runtime.local_doc_paths()
    assert paths.ok is True
    assert "README.md" in paths.summary
    assert "docs/TOOLS.md" in paths.summary

    search = runtime.local_doc_search("release checks")
    assert search.ok is True
    assert search.data["results"][0]["path"] == "README.md"

    read = runtime.local_doc_read("docs/TOOLS.md")
    assert read.ok is True
    assert "Old docs line" in read.summary

    blocked = runtime.local_doc_replace("docs/TOOLS.md", "Old docs line", "New docs line")
    assert blocked.ok is False
    assert "Confirmation required" in blocked.summary

    replaced = runtime.local_doc_replace("docs/TOOLS.md", "Old docs line", "New docs line", confirm=True)
    assert replaced.ok is True
    assert "New docs line" in runtime.local_doc_read("docs/TOOLS.md").summary

    non_doc = runtime.local_doc_replace("src.py", "Old docs line", "New docs line", confirm=True)
    assert non_doc.ok is False


def test_search_index_memory_task_and_observability_tools(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    runtime.write_file(
        "pkg/demo.py",
        "class Demo:\n    pass\n\n\ndef helper():\n    return 'router'\n",
    )
    runtime.write_file("notes.txt", "router and catalog summary\nsecond line\n")

    grep_result = runtime.grep_search("router")
    assert grep_result.ok is True
    assert "notes.txt" in grep_result.summary or "pkg/demo.py" in grep_result.summary

    symbol_result = runtime.find_symbol("Demo")
    assert symbol_result.ok is True
    assert "class Demo" in symbol_result.summary

    build = runtime.build_index()
    assert build.ok is True
    query = runtime.query_index("router catalog")
    assert query.ok is True
    sources = runtime.list_indexed_sources()
    assert sources.ok is True
    assert "notes.txt" in sources.summary
    assert runtime.update_index().ok is True
    assert runtime.delete_from_index("notes.txt").ok is True

    assert runtime.save_memory("favorite", {"tool": "grep_search"}).ok is True
    assert runtime.create_memory("tone", "direct").ok is True
    assert runtime.load_memory("favorite").ok is True
    assert runtime.update_memory("favorite", {"tool": "query_index"}).ok is True
    assert runtime.edit_memory("tone", "detailed").ok is True
    memories = runtime.list_memories()
    assert memories.ok is True
    assert "favorite" in memories.summary

    planned = runtime.plan_task("demo", ["discover", "verify"])
    assert planned.ok is True
    task_id = planned.data["task_id"]
    assert runtime.execute_step(task_id, 0).ok is True
    assert runtime.mark_step_complete(task_id, 0).ok is True
    assert runtime.retry_step(task_id, 1).ok is True
    assert runtime.task_checkpoint(task_id, "halfway there").ok is True
    assert runtime.load_checkpoint(task_id).ok is True
    status = runtime.get_task_status(task_id)
    assert status.ok is True
    assert runtime.abort_task(task_id).ok is True

    assert runtime.log_event("custom", {"value": 1}).ok is True
    assert runtime.trace_step(task_id, "grep_search").ok is True
    assert runtime.record_tool_latency("grep_search", 12).ok is True
    assert runtime.record_error("boom", {"tool": "grep_search"}).ok is True
    replay = runtime.replay_session()
    assert replay.ok is True
    assert "custom" in replay.summary
    assert runtime.summarize_session().ok is True
    assert runtime.summarize_run().ok is True

    assert runtime.request_user_approval("git reset", confirm=False).ok is False
    assert runtime.check_permission("git reset", risky=True, confirm=False).ok is False
    assert runtime.log_sensitive_action("git_reset", {"target": "HEAD~1"}).ok is True
    assert runtime.sandbox_shell_execution("rm tmp.txt", confirm=False).ok is False
    assert runtime.delete_memory("favorite").ok is True
    assert runtime.delete_memory("tone").ok is True
    assert runtime.plan_task("empty", []).ok is False

    empty_root = tmp_path / "other"
    empty_root.mkdir()
    indexed_empty = make_runtime(empty_root)
    assert indexed_empty.list_indexed_sources().ok is False


def test_web_tools_with_local_http_server_and_stubbed_search(tmp_path: Path):
    runtime = make_runtime(tmp_path)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/page":
                body = b"<html><body><h1>Demo</h1><p>Hello world</p></body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path == "/data":
                payload = json.dumps({"name": "demo", "ok": True}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            body = b"downloaded"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        blocked_local = runtime.fetch_url(f"{base_url}/page")
        assert blocked_local.ok is False
        assert "SSRF protection" in blocked_local.summary

        fetched = runtime.fetch_url(f"{base_url}/page", confirm=True)
        assert fetched.ok is True
        assert "Hello world" in fetched.summary
        assert fetched.data["status"] == 200
        assert fetched.data["content_type"].startswith("text/html")

        expanded_blocked = runtime.expand_search_result(f"{base_url}/page")
        assert expanded_blocked.ok is False
        assert "SSRF protection" in expanded_blocked.summary

        extracted = runtime.extract_webpage_content(url=f"{base_url}/page", confirm=True)
        assert extracted.ok is True
        assert "Demo" in extracted.summary
        assert "Hello world" in extracted.summary

        parsed = runtime.parse_json_api(f"{base_url}/data", confirm=True)
        assert parsed.ok is True
        assert parsed.data["ok"] is True

        downloaded = runtime.download_file(f"{base_url}/file", "download.txt", confirm=True)
        assert downloaded.ok is True
        assert runtime.read_file("download.txt").summary == "downloaded"

        metadata = runtime.fetch_url("http://169.254.169.254/latest/meta-data/")
        assert metadata.ok is False
        assert "metadata IP" in metadata.summary

        rejected = runtime.fetch_url("file:///etc/passwd")
        assert rejected.ok is False
        assert "http://" in rejected.summary

        runtime.fetch_url = lambda url, confirm=False: ToolCall(
            "fetch_url",
            True,
            json.dumps(
                {
                    "AbstractText": "DuckDuckGo style summary",
                    "RelatedTopics": [{"Text": "Related result"}],
                }
            ),
            {"url": url},
        )
        search = runtime.web_search("tooling showcase")
        assert search.ok is True
        assert "DuckDuckGo style summary" in search.summary

        def html_fallback(url, confirm=False):
            if "api.duckduckgo.com" in url:
                return ToolCall("fetch_url", True, json.dumps({}), {"url": url})
            return ToolCall(
                "fetch_url",
                True,
                '<html><body><article><a class="result__a" href="https://example.com/doc">Example Docs</a><div class="result__snippet">Structured outputs guide</div></article></body></html>',
                {"url": url},
            )

        runtime.fetch_url = html_fallback
        html_search = runtime.web_search("structured outputs")
        assert html_search.ok is True
        assert "Example Docs" in html_search.summary
        assert html_search.data["results"][0]["snippet"] == "Structured outputs guide"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def test_search_result_ranking_prefers_official_ags_docs(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    ranked = runtime._rank_search_results(
        "official AGS docs toggle window",
        [
            {
                "title": "AGS Resources",
                "snippet": "old AGS links",
                "url": "https://www.americangirlscouts.org/agsresources/modules.html",
            },
            {
                "title": "CLI - AGS Wiki",
                "snippet": "Toggle Window -- toggle-window",
                "url": "https://aylur.github.io/ags-docs/config/cli/",
            },
        ],
    )
    assert ranked[0]["url"] == "https://aylur.github.io/ags-docs/config/cli/"


def test_web_expansion_and_current_data_tools(tmp_path: Path):
    runtime = make_runtime(tmp_path)

    rewritten = runtime._web_search_query_for_context("latest linux kernel stable version")
    assert "as of " in rewritten
    explicit = runtime._web_search_query_for_context("weather in London on 2026-04-25")
    assert explicit == "weather in London on 2026-04-25"

    runtime.fetch_url = lambda url, confirm=False: ToolCall(
        "fetch_url",
        True,
        "<html><body><main>Linux kernel stable release is 6.12 and request handlers use ags request say hi in docs.</main></body></html>",
        {"url": url},
    )
    expanded = runtime.expand_search_result("https://example.com", query="ags request")
    assert expanded.ok is True
    assert "ags request" in expanded.summary

    runtime.web_search = lambda query, confirm=False: ToolCall(
        "web_search",
        True,
        "top search",
        {
            "query": query,
            "results": [
                {"title": "Doc One", "url": "https://example.com/one"},
                {"title": "Doc Two", "url": "https://example.com/two"},
            ],
        },
    )
    expanded_results = runtime.expand_search_results("ags request", limit=2)
    assert expanded_results.ok is True
    assert "Doc One" in expanded_results.summary

    runtime.parse_json_api = lambda url, confirm=False: ToolCall(
        "parse_json_api",
        True,
        "json ok",
        {
            "results": [
                {
                    "name": "London",
                    "country": "United Kingdom",
                    "latitude": 51.5,
                    "longitude": -0.1,
                    "timezone": "Europe/London",
                }
            ]
        }
        if "geocoding-api" in url
        else {
            "current": {
                "time": "2026-04-22T17:00",
                "temperature_2m": 15,
                "apparent_temperature": 14,
                "weather_code": 0,
                "wind_speed_10m": 12,
            },
            "hourly": {
                "time": ["2026-04-22T17:00", "2026-04-22T18:00"],
                "temperature_2m": [15, 14],
                "apparent_temperature": [14, 13],
                "weather_code": [0, 1],
                "precipitation_probability": [5, 10],
                "wind_speed_10m": [12, 8],
            },
        },
    )
    weather = runtime.weather_lookup(query="weather in London tonight")
    assert weather.ok is True
    assert "Weather for London, United Kingdom" in weather.summary

    runtime.parse_json_api = lambda url, confirm=False: ToolCall(
        "parse_json_api",
        True,
        "json ok",
        {
            "releases": [
                {"moniker": "stable", "version": "6.12.1", "released": {"isodate": "2026-04-20"}},
                {"moniker": "longterm", "version": "6.6.88", "released": {"isodate": "2026-04-18"}},
                {"moniker": "mainline", "version": "7.0", "released": {"isodate": "2026-04-12"}},
            ]
        },
    )
    kernel = runtime.latest_linux_kernel()
    assert kernel.ok is True
    assert "Stable: 6.12.1" in kernel.summary


def test_shell_dev_and_git_tools(tmp_path: Path, monkeypatch):
    runtime = make_runtime(tmp_path, project_equals_workspace=True)
    workspace = runtime.config.workspace_root
    script_path = workspace / "script.py"
    script_path.write_text("print('script ok')\n", encoding="utf-8")

    safe_shell = runtime.safe_shell_command('python -c "print(7)"')
    assert safe_shell.ok is True
    assert safe_shell.summary.strip() == "7"
    assert runtime.safe_shell_command('python -c "print(1)" && pwd').ok is False

    shell_blocked = runtime.shell_command("rm temp.txt", confirm=False)
    assert shell_blocked.ok is False

    assert runtime.process_list().ok is True
    assert runtime.system_info().ok is True
    env_result = runtime.env_vars(prefix="PATH")
    assert env_result.ok is True
    assert "PATH=" in env_result.summary

    assert runtime.execute_script("script.py").ok is True
    assert runtime.run_tests("python -c 'print(\"tests ok\")'").ok is True
    assert runtime.lint_code("python -c 'print(\"lint ok\")'").ok is True
    assert runtime.format_code("python -c 'print(\"format ok\")'").ok is True
    assert runtime.build_project("python -c 'print(\"build ok\")'").ok is True
    assert runtime.install_dependencies("python -c 'print(\"deps ok\")'").ok is True

    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
    default_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=workspace,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Showcase Bot")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "showcase@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Showcase Bot")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "showcase@example.com")

    (workspace / "tracked.txt").write_text("one\n", encoding="utf-8")
    assert runtime.git_add(["tracked.txt"]).ok is True
    assert runtime.git_commit("initial commit").ok is True
    assert runtime.git_status().ok is True
    assert runtime.git_log().ok is True

    (workspace / "tracked.txt").write_text("one\ntwo\n", encoding="utf-8")
    assert runtime.git_diff().ok is True
    assert runtime.git_branch("feature", create=True).ok is True
    assert runtime.git_checkout("feature").ok is True
    (workspace / "feature.txt").write_text("feature\n", encoding="utf-8")
    assert runtime.git_add(["feature.txt"]).ok is True
    assert runtime.git_commit("feature commit").ok is True
    assert runtime.git_checkout(default_branch).ok is True
    assert runtime.git_merge("feature").ok is True

    (workspace / "tracked.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    assert runtime.git_add(["tracked.txt"]).ok is True
    assert runtime.git_commit("third commit").ok is True
    assert runtime.git_reset(confirm=False).ok is False
    assert runtime.git_reset(confirm=True).ok is True

    (workspace / "tracked.txt").write_text("stash me\n", encoding="utf-8")
    assert runtime.git_stash().ok is True


def test_shell_policy_parses_executables_and_argument_patterns(tmp_path: Path):
    runtime = make_runtime(tmp_path, project_equals_workspace=True)

    sudo = runtime.shell_command("sudo", confirm=True)
    assert sudo.ok is False
    assert "exec:sudo" in sudo.data["blocked"]

    root_delete = runtime.shell_command("rm -fr /", confirm=True)
    assert root_delete.ok is False
    assert "args:rm -rf /" in root_delete.data["blocked"]

    disk_redirect = runtime.shell_command("echo hi >/dev/sda", confirm=True)
    assert disk_redirect.ok is False
    assert "redirect:/dev/sd" in disk_redirect.data["blocked"]

    git_reset = runtime.shell_command("git -C . reset --hard", confirm=False)
    assert git_reset.ok is False
    assert "git:reset" in git_reset.data["risky"]

    quoted_text = runtime.shell_command("python -c \"print('rm temp.txt')\"", confirm=False)
    assert quoted_text.ok is True
    assert quoted_text.summary == "rm temp.txt"


def test_manual_mutation_tools_require_confirmation_and_type_errors_do_not_retry(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    blocked = runtime.run_tool("write_file", {"path": "owned.txt", "content": "owned"}, confirm=False)
    assert blocked.ok is False
    assert blocked.data["requires_confirmation"] is True
    assert not (runtime.config.workspace_root / "owned.txt").exists()

    allowed = runtime.run_tool("write_file", {"path": "owned.txt", "content": "owned"}, confirm=True)
    assert allowed.ok is True
    assert (runtime.config.workspace_root / "owned.txt").read_text(encoding="utf-8") == "owned"

    calls = {"count": 0}

    def boom(value: str):
        calls["count"] += 1
        raise TypeError("internal type problem")

    runtime.boom = boom
    failed = runtime.run_tool("boom", {"value": "x"})
    assert failed.ok is False
    assert calls["count"] == 1


def test_tool_stats_tracking_success(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    workspace = tmp_path / "workspace"
    (workspace / "test.txt").write_text("content", encoding="utf-8")

    runtime.run_tool("read_file", {"path": "test.txt"})

    stats = runtime._load_tool_stats()
    assert "read_file" in stats
    assert stats["read_file"]["successes"] >= 1


def test_tool_stats_tracking_failure(tmp_path: Path):
    runtime = make_runtime(tmp_path)

    runtime.run_tool("read_file", {"path": "nonexistent.txt"})

    stats = runtime._load_tool_stats()
    assert "read_file" in stats
    assert stats["read_file"]["failures"] >= 1


def test_tool_stats_persistence(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    workspace = tmp_path / "workspace"
    (workspace / "test.txt").write_text("content", encoding="utf-8")

    runtime.run_tool("read_file", {"path": "test.txt"})

    stats_path = runtime._tool_stats_path
    assert stats_path.exists()

    from tooling_showcase.tools import ToolRuntime

    runtime2 = ToolRuntime(runtime.config)

    stats = runtime2._load_tool_stats()
    assert "read_file" in stats
    assert stats["read_file"]["successes"] >= 1


def test_runtime_uses_fallback_state_dir_when_repo_state_files_not_writable(
    tmp_path: Path, monkeypatch
):
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("root can write chmod-read-only files")

    fallback_root = tmp_path / "xdg-state"
    monkeypatch.setenv("XDG_STATE_HOME", str(fallback_root))

    runtime = make_runtime(tmp_path)
    repo_state = tmp_path / "state"
    repo_state.mkdir(parents=True, exist_ok=True)
    blocked = repo_state / "tasks.json"
    blocked.write_text("{}", encoding="utf-8")
    blocked.chmod(0o444)

    from tooling_showcase.tools import ToolRuntime

    runtime = ToolRuntime(runtime.config)
    assert runtime.state_root == fallback_root / "tooling-showcase" / tmp_path.name
    result = runtime.plan_task("fallback", ["step one"])
    assert result.ok is True


def test_optional_and_validation_tools(tmp_path: Path):
    runtime = make_runtime(tmp_path)

    assert runtime.extract_webpage_content().ok is False
    assert runtime.build_index("missing").ok is False

    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn0YxkAAAAASUVORK5CYII="
    )
    image_path = runtime.config.workspace_root / "pixel.png"
    image_path.write_bytes(png_bytes)

    image_result = runtime.analyze_image("pixel.png")
    assert image_result.ok is True
    assert image_result.data["mime_type"] == "image/png"
    assert image_result.data["size_bytes"] > 0

    if "width" in image_result.data:
        assert image_result.data["width"] == 1
        assert image_result.data["height"] == 1

    device_result = runtime.control_device("lights on")
    assert device_result.ok is True
    log_path = runtime.state_root / "device_commands.jsonl"
    assert log_path.exists() is True
    assert "lights on" in log_path.read_text(encoding="utf-8")
