from __future__ import annotations

from dataclasses import asdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen
import inspect
import json
import subprocess

from tooling_showcase.adapters import WorkspaceAdapters
from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.library_tools import LocalLibrary
from tooling_showcase.models import ToolCall
from tooling_showcase.retrieval import (
    build_chunks,
    load_index,
    query_chunks,
    save_index,
)


TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
    ".sh",
}


class _DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_result = False
        self._href: str | None = None
        self._title_parts: list[str] = []
        self.results: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs):
        attr_map = dict(attrs)
        if tag == "a" and attr_map.get("class") == "result__a":
            self._in_result = True
            self._href = attr_map.get("href")
            self._title_parts = []

    def handle_data(self, data: str):
        if self._in_result:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str):
        if tag == "a" and self._in_result:
            title = " ".join(part.strip() for part in self._title_parts if part.strip())
            if title and self._href:
                self.results.append({"title": title, "url": self._href})
            self._in_result = False
            self._href = None
            self._title_parts = []


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str):
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str):
        if self._skip_depth:
            return
        stripped = " ".join(data.split())
        if stripped:
            self.parts.append(stripped)

    def text(self) -> str:
        return " ".join(self.parts)


class ToolRuntime:
    def __init__(self, config: ShowcaseConfig) -> None:
        self.config = config
        self.state_root = self._choose_state_root()
        self.index_path = self.state_root / "local_index.json"
        self.task_path = self.state_root / "tasks.json"
        self.memory_path = self.state_root / "memories.json"
        self.checkpoint_path = self.state_root / "checkpoints.json"
        self.device_log_path = self.state_root / "device_commands.jsonl"
        self._tool_stats_path = self.state_root / "tool_stats.json"
        self.aliases = {
            "search_text": "grep_search",
            "patch_file": "apply_patch",
            "rename_file": "move_file",
        }
        self.adapters = WorkspaceAdapters(config.portfolio_root)
        self.library = LocalLibrary.from_env()
        self.state_root.mkdir(parents=True, exist_ok=True)

    def run_tool(self, name: str, arguments: dict | None = None, *, confirm: bool = False) -> ToolCall:
        arguments = arguments or {}
        name = self.aliases.get(name, name)
        if name == "read_file" and "path" in arguments and "path_text" not in arguments:
            arguments = {**arguments, "path_text": arguments["path"]}
            arguments.pop("path", None)
        handler = getattr(self, name, None)
        if handler is None:
            call = ToolCall(name, False, f"Unknown tool: {name}")
            self._record_tool_stat(name, call.ok)
            return call
        try:
            call_arguments = dict(arguments)
            if "confirm" not in call_arguments:
                signature = inspect.signature(handler)
                if "confirm" in signature.parameters:
                    call_arguments["confirm"] = confirm
            try:
                call = handler(**call_arguments)
            except TypeError:
                call = handler(arguments)
        except TypeError as e:
            call = ToolCall(name, False, f"Invalid arguments: {e}")
        except Exception as e:
            call = ToolCall(name, False, f"Tool failed: {e}")
        self._record_tool_stat(name, bool(getattr(call, "ok", False)))
        return call

    def available_tools(self) -> list[str]:
        return [
            "abort_task",
            "adapter_inventory",
            "analyze_image",
            "append_file",
            "apply_patch",
            "build_index",
            "build_project",
            "calculate",
            "check_permission",
            "content_search",
            "control_device",
            "convert_units",
            "copy_file",
            "create_file",
            "datetime_now",
            "delete_file",
            "delete_from_index",
            "delete_memory",
            "draft_system_prompt",
            "download_file",
            "encode_decode",
            "env_vars",
            "execute_script",
            "execute_step",
            "expand_search_result",
            "expand_search_results",
            "extract_webpage_content",
            "fetch_url",
            "file_search",
            "find_symbol",
            "format_code",
            "generate_uuid",
            "get_file_info",
            "get_task_status",
            "git_add",
            "git_branch",
            "git_checkout",
            "git_commit",
            "git_diff",
            "git_log",
            "git_merge",
            "git_reset",
            "git_stash",
            "git_status",
            "grep_search",
            "hash_file",
            "install_dependencies",
            "kill_process",
            "latest_linux_kernel",
            "library_info",
            "library_read_epub",
            "library_read_zim",
            "library_search",
            "lint_code",
            "list_directory",
            "list_indexed_sources",
            "list_memories",
            "load_checkpoint",
            "load_memory",
            "log_event",
            "log_sensitive_action",
            "mark_step_complete",
            "move_file",
            "parse_json_api",
            "parse_pdf",
            "plan_task",
            "process_list",
            "query_index",
            "record_error",
            "record_tool_latency",
            "read_file",
            "replay_session",
            "request_user_approval",
            "retry_step",
            "run_model",
            "run_tests",
            "safe_shell_command",
            "sandbox_file_access",
            "sandbox_shell_execution",
            "save_memory",
            "screenshot_page",
            "shell_command",
            "summarize_run",
            "summarize_session",
            "system_info",
            "task_checkpoint",
            "text_to_speech",
            "tree_view",
            "trace_step",
            "transcribe_audio",
            "update_index",
            "update_memory",
            "web_search",
            "weather_lookup",
            "write_file",
        ]

    def _now(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def file_search(self, query: str) -> ToolCall:
        matches: list[str] = []
        for path in self.config.workspace_root.rglob("*"):
            if not path.is_file():
                continue
            if any(
                part.startswith(".")
                for part in path.relative_to(self.config.workspace_root).parts
            ):
                continue
            if query.lower() in path.name.lower():
                matches.append(str(path))
            if len(matches) >= 25:
                break
        summary = json.dumps(matches, indent=2) if matches else "[]"
        return ToolCall(
            tool_name="file_search",
            ok=True,
            summary=summary,
            data={"matches": matches},
        )

    def read_file(self, path_text: str) -> ToolCall:
        target = self._resolve_path(path_text)
        if target is None or not target.exists() or not target.is_file():
            return ToolCall("read_file", False, f"File not found: {path_text}")
        if target.suffix.lower() not in TEXT_EXTENSIONS:
            return ToolCall(
                "read_file", False, f"Unsupported text file type: {target.name}"
            )
        text = target.read_text(encoding="utf-8", errors="replace")
        if len(text) > 8000:
            text = text[:8000] + "\n... [truncated]"
        return ToolCall(
            tool_name="read_file",
            ok=True,
            summary=text,
            data={"path": str(target)},
        )

    def content_search(self, query: str) -> ToolCall:
        if not query.strip():
            return ToolCall("content_search", False, "Search query is empty.")
        matches: list[dict[str, str | int]] = []
        pattern = query.lower()
        for path in self.config.workspace_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            if any(
                part.startswith(".")
                for part in path.relative_to(self.config.workspace_root).parts
            ):
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line_no, line in enumerate(lines, start=1):
                if pattern in line.lower():
                    matches.append(
                        {
                            "path": str(path),
                            "line": line_no,
                            "text": line[:240],
                        }
                    )
                    if len(matches) >= 25:
                        break
            if len(matches) >= 25:
                break
        rendered = "\n".join(
            f"{item['path']}:{item['line']}: {item['text']}" for item in matches
        )
        return ToolCall(
            tool_name="content_search",
            ok=True,
            summary=rendered or "No matching content found.",
            data={"matches": matches},
        )

    def query_index(self, query: str) -> ToolCall:
        chunks = load_index(self.index_path)
        if not chunks:
            return ToolCall(
                tool_name="query_index",
                ok=False,
                summary="No index found. Build an index first.",
                data={"path": str(self.index_path)},
            )
        selected = query_chunks(chunks, query=query)
        rendered = "\n\n".join(
            f"Source: {chunk.label} [{chunk.start_line}-{chunk.end_line}]\n{chunk.text}"
            for chunk in selected
        )
        return ToolCall(
            tool_name="query_index",
            ok=True,
            summary=rendered,
            data={"matches": len(selected)},
        )

    def expand_search_result(self, url: str, query: str | None = None) -> ToolCall:
        url = self._normalize_search_url(url)
        fetched = self.fetch_url(url)
        if not fetched.ok:
            return ToolCall("expand_search_result", False, f"Failed to fetch URL: {fetched.summary}")
        text = self._extract_text_from_html(fetched.summary, query=query)
        return ToolCall(
            tool_name="expand_search_result",
            ok=True,
            summary=text[:8000],
            data={"url": url, "query": query},
        )

    def _extract_text_from_html(self, html: str, query: str | None = None) -> str:
        parser = _HTMLTextExtractor()
        parser.feed(html)
        text = parser.text()
        if not query:
            return text
        query_lower = query.lower()
        text_lower = text.lower()
        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:2000]
        start = max(0, pos - 200)
        end = min(len(text), pos + len(query) + 800)
        return text[start:end]

    def _normalize_search_url(self, url: str) -> str:
        normalized = url.strip()
        if normalized.startswith("//"):
            normalized = "https:" + normalized
        parsed = urlparse(normalized)
        if "duckduckgo.com" in parsed.netloc and parsed.path == "/l/":
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            if target:
                return unquote(target)
        return normalized

    def shell_command(self, command: str, confirm: bool = False) -> ToolCall:
        normalized = f" {command.strip()} "
        blocked = [
            token
            for token in self.config.shell_policy.blocked_substrings
            if token in normalized
        ]
        if blocked:
            return ToolCall(
                tool_name="shell_command",
                ok=False,
                summary="Blocked shell command by safety policy.",
                data={"command": command, "blocked": blocked},
            )
        risky = [
            token
            for token in self.config.shell_policy.risky_substrings
            if token in normalized
        ]
        if (
            risky
            and self.config.shell_policy.require_confirmation_for_risky
            and not confirm
        ):
            return ToolCall(
                tool_name="shell_command",
                ok=False,
                summary="Confirmation required for risky shell command.",
                data={"command": command, "risky": risky},
            )
        try:
            completed = subprocess.run(
                ["bash", "-lc", command],
                capture_output=True,
                text=True,
                cwd=str(self.config.workspace_root),
                check=False,
                timeout=self.config.shell_policy.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return ToolCall(
                tool_name="shell_command",
                ok=False,
                summary="Shell command timed out.",
                data={"command": command},
            )
        output = completed.stdout.strip() or completed.stderr.strip() or "[no output]"
        max_output = self.config.shell_policy.max_output_chars
        if len(output) > max_output:
            output = output[:max_output] + "\n... [truncated]"
        return ToolCall(
            tool_name="shell_command",
            ok=completed.returncode == 0,
            summary=output,
            data={"command": command, "returncode": completed.returncode},
        )

    def adapter_inventory(self) -> ToolCall:
        cards = self.adapters.cards()
        rendered = []
        for card in cards:
            rendered.append(f"- {card.name}: {card.status} | {card.summary}")
        return ToolCall(
            tool_name="adapter_inventory",
            ok=True,
            summary="\n".join(rendered),
            data={"cards": [asdict(card) for card in cards]},
        )

    def library_info(self, arguments: dict | None = None, *, confirm: bool = False):
        return ToolCall(
            tool_name="library_info",
            ok=True,
            summary=json.dumps(self.library.info(), indent=2),
            data=self.library.info(),
        )

    def library_search(self, arguments: dict | None = None, *, confirm: bool = False):
        arguments = arguments or {}
        query = str(arguments.get("query", "")).strip()
        limit = int(arguments.get("limit", 10))
        results = self.library.search(query, limit=limit)
        if not results:
            return ToolCall(
                tool_name="library_search",
                ok=True,
                summary=f"No library results found for: {query}",
                data={"results": []},
            )
        summary = "\n\n".join(
            f"{item['id']} | {item['title']} | {item['type']}\n{item['path']}\n{item.get('snippet', '')}"
            for item in results
        )
        return ToolCall(
            tool_name="library_search",
            ok=True,
            summary=summary,
            data={"results": results},
        )

    def library_read_epub(self, arguments: dict | None = None, *, confirm: bool = False):
        arguments = arguments or {}
        item_id = str(arguments.get("id", "")).strip()
        query = str(arguments.get("query", "")).strip()
        max_chars = int(arguments.get("max_chars", 12000))
        result = self.library.read_epub(item_id, query=query, max_chars=max_chars)
        return ToolCall(
            tool_name="library_read_epub",
            ok=bool(result.get("ok")),
            summary=result.get("text") or result.get("error", ""),
            data=result,
        )

    def tree_view(self, path: str = ".", max_depth: int = 4) -> ToolCall:
        root = self._resolve_path(path) if path else self.config.workspace_root
        if root is None or not root.exists():
            return ToolCall("tree_view", False, f"Path not found: {path}")

        max_depth = max(1, min(int(max_depth or 1), 8))
        lines = [root.name or "."]

        def walk(directory: Path, prefix: str, depth: int) -> None:
            if depth >= max_depth or len(lines) >= 300:
                return
            try:
                children = sorted(
                    [item for item in directory.iterdir() if not item.name.startswith(".")],
                    key=lambda x: (not x.is_dir(), x.name.lower()),
                )
            except OSError:
                return
            for item in children[:100]:
                suffix = "/" if item.is_dir() else ""
                lines.append(f"{prefix}{item.name}{suffix}")
                if item.is_dir():
                    walk(item, prefix + "  ", depth + 1)

        try:
            if root.is_dir():
                walk(root, "  ", 0)
        except OSError as e:
            return ToolCall("tree_view", False, f"Cannot list: {e}")
        return ToolCall(
            tool_name="tree_view",
            ok=True,
            summary="\n".join(lines),
            data={"path": str(root)},
        )

    def library_read_zim(self, arguments: dict | None = None, *, confirm: bool = False):
        arguments = arguments or {}
        item_id = arguments.get("id", "")
        title = arguments.get("title", "")

        result = self.library.read_zim(item_id, title)

        return ToolCall(
            tool_name="library_read_zim",
            ok=result.get("ok", False),
            summary=result.get("text") or result.get("error", ""),
            data=result,
        )

    def maybe_contextual_tool_calls(self, text: str) -> list[ToolCall]:
        lowered = text.lower()
        calls: list[ToolCall] = []
        if any(
            token in lowered
            for token in ("readme", "pyproject", "router", "index", "tool")
        ):
            calls.append(self.file_search("README" if "readme" in lowered else ""))
        if any(
            token in lowered
            for token in ("docs", "documentation", "ollama", "tool calling")
        ):
            calls.append(self.web_search(text))
        if any(
            token in lowered
            for token in ("source project", "workspace", "showcase", "adapter")
        ):
            calls.append(self.adapter_inventory())
        return [call for call in calls if call.summary]

    def _resolve_path(self, path_text: str) -> Path | None:
        raw = path_text.strip().strip('"').strip("'")
        candidate = Path(raw)
        if candidate.is_absolute():
            resolved = candidate.resolve()
            return resolved if self._allowed(resolved) else None
        direct = (self.config.workspace_root / candidate).resolve()
        if direct.exists() and self._allowed(direct):
            return direct
        for match in self.config.workspace_root.rglob(candidate.name):
            resolved = match.resolve()
            if self._allowed(resolved):
                return resolved
        return None

    def _allowed(self, path: Path) -> bool:
        try:
            path.relative_to(self.config.workspace_root)
            return True
        except ValueError:
            return False

    def _choose_state_root(self) -> Path:
        import os

        repo_state = self.config.project_root / "state"
        state_files = [
            repo_state / "tasks.json",
            repo_state / "memories.json",
            repo_state / "tool_stats.json",
        ]
        repo_unusable = repo_state.exists() and not os.access(repo_state, os.W_OK)
        repo_unusable = repo_unusable or any(
            path.exists() and not os.access(path, os.W_OK) for path in state_files
        )
        if repo_unusable:
            fallback = Path.home()
            fallback = Path(os.getenv("XDG_STATE_HOME", str(fallback / ".local" / "state")))
            return fallback / "tooling-showcase" / self.config.project_root.name
        return repo_state

    def _workspace_path(self, path_text: str) -> Path | None:
        raw = str(path_text or ".").strip().strip('"').strip("'")
        candidate = Path(raw)
        resolved = candidate.resolve() if candidate.is_absolute() else (self.config.workspace_root / candidate).resolve()
        return resolved if self._allowed(resolved) else None

    def _load_json(self, path: Path, default):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def _save_json(self, path: Path, payload) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8", newline="\n")

    def _record_tool_stat(self, name: str, ok: bool) -> None:
        stats = self._load_tool_stats()
        row = stats.setdefault(name, {"successes": 0, "failures": 0})
        row["successes" if ok else "failures"] = int(row.get("successes" if ok else "failures", 0)) + 1
        self._save_json(self._tool_stats_path, stats)

    def _load_tool_stats(self) -> dict:
        return self._load_json(self._tool_stats_path, {})

    def write_file(self, path: str, content: str) -> ToolCall:
        target = self._workspace_path(path)
        if target is None:
            return ToolCall("write_file", False, f"Path escapes workspace: {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        return ToolCall("write_file", True, f"Wrote {target.relative_to(self.config.workspace_root)}", {"path": str(target)})

    def create_file(self, path: str, content: str = "") -> ToolCall:
        target = self._workspace_path(path)
        if target is None:
            return ToolCall("create_file", False, f"Path escapes workspace: {path}")
        if target.exists():
            return ToolCall("create_file", False, f"File already exists: {path}")
        return self.write_file(path, content)

    def append_file(self, path: str, content: str) -> ToolCall:
        target = self._workspace_path(path)
        if target is None:
            return ToolCall("append_file", False, f"Path escapes workspace: {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return ToolCall("append_file", True, f"Appended {target.relative_to(self.config.workspace_root)}", {"path": str(target)})

    def apply_patch(self, path: str, old: str, new: str) -> ToolCall:
        target = self._workspace_path(path)
        if target is None or not target.exists():
            return ToolCall("apply_patch", False, f"File not found: {path}")
        text = target.read_text(encoding="utf-8", errors="replace")
        if old not in text:
            return ToolCall("apply_patch", False, "Patch text not found.")
        target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
        return ToolCall("apply_patch", True, f"Patched {path}")

    def delete_file(self, path: str) -> ToolCall:
        target = self._workspace_path(path)
        if target is None or not target.exists() or not target.is_file():
            return ToolCall("delete_file", False, f"File not found: {path}")
        target.unlink()
        return ToolCall("delete_file", True, f"Deleted {path}")

    def copy_file(self, source: str, destination: str) -> ToolCall:
        import shutil

        src = self._workspace_path(source)
        dst = self._workspace_path(destination)
        if src is None or dst is None or not src.exists():
            return ToolCall("copy_file", False, "Source missing or path escapes workspace.")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return ToolCall("copy_file", True, f"Copied {source} to {destination}")

    def move_file(self, source: str, destination: str) -> ToolCall:
        import shutil

        src = self._workspace_path(source)
        dst = self._workspace_path(destination)
        if src is None or dst is None or not src.exists():
            return ToolCall("move_file", False, "Source missing or path escapes workspace.")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return ToolCall("move_file", True, f"Moved {source} to {destination}")

    def list_directory(self, path: str = ".") -> ToolCall:
        root = self._workspace_path(path)
        if root is None or not root.exists() or not root.is_dir():
            return ToolCall("list_directory", False, f"Directory not found: {path}")
        names = sorted(item.name + ("/" if item.is_dir() else "") for item in root.iterdir() if not item.name.startswith("."))
        return ToolCall("list_directory", True, "\n".join(names), {"path": str(root), "entries": names})

    def get_file_info(self, path: str) -> ToolCall:
        target = self._workspace_path(path)
        if target is None or not target.exists():
            return ToolCall("get_file_info", False, f"Path not found: {path}")
        stat = target.stat()
        data = {"path": str(target), "size": stat.st_size, "is_file": target.is_file(), "is_dir": target.is_dir()}
        return ToolCall("get_file_info", True, json.dumps(data, sort_keys=True), data)

    def hash_file(self, path: str, algorithm: str = "sha256") -> ToolCall:
        import hashlib

        target = self._workspace_path(path)
        if target is None or not target.exists() or not target.is_file():
            return ToolCall("hash_file", False, f"File not found: {path}")
        digest = hashlib.new(algorithm)
        digest.update(target.read_bytes())
        return ToolCall("hash_file", True, digest.hexdigest(), {"algorithm": algorithm})

    def sandbox_file_access(self, path: str) -> ToolCall:
        target = self._workspace_path(path)
        return ToolCall("sandbox_file_access", target is not None, "Allowed" if target else "Path escapes workspace")

    def grep_search(self, query: str) -> ToolCall:
        call = self.content_search(query)
        call.tool_name = "grep_search"
        return call

    def find_symbol(self, symbol: str) -> ToolCall:
        matches = []
        needles = (f"class {symbol}", f"def {symbol}", f"function {symbol}")
        for path in self.config.workspace_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if any(needle in line for needle in needles):
                    matches.append(f"{path}:{line_no}: {line}")
        return ToolCall("find_symbol", True, "\n".join(matches) or "No symbol found.")

    def build_index(self, path: str = ".") -> ToolCall:
        root = self._workspace_path(path)
        if root is None or not root.exists():
            return ToolCall("build_index", False, f"Path not found: {path}")
        documents: dict[str, str] = {}
        paths = [root] if root.is_file() else root.rglob("*")
        for item in paths:
            if not item.is_file() or item.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            if any(part.startswith(".") for part in item.relative_to(self.config.workspace_root).parts):
                continue
            documents[str(item)] = item.read_text(encoding="utf-8", errors="replace")
            if len(documents) >= 200:
                break
        chunks = build_chunks(documents)
        save_index(chunks, self.index_path)
        return ToolCall("build_index", True, f"Indexed {len(documents)} documents into {len(chunks)} chunks.", {"documents": len(documents), "chunks": len(chunks), "path": str(self.index_path)})

    def update_index(self) -> ToolCall:
        return self.build_index()

    def list_indexed_sources(self) -> ToolCall:
        chunks = load_index(self.index_path)
        if not chunks:
            return ToolCall("list_indexed_sources", False, "No index found.")
        sources = sorted({chunk.label for chunk in chunks})
        return ToolCall("list_indexed_sources", True, "\n".join(sources), {"sources": sources})

    def delete_from_index(self, source: str) -> ToolCall:
        chunks = [chunk for chunk in load_index(self.index_path) if source not in chunk.label and source not in chunk.document_id]
        save_index(chunks, self.index_path)
        return ToolCall("delete_from_index", True, f"Removed matching chunks for {source}.", {"chunks": len(chunks)})

    def save_memory(self, key: str, value) -> ToolCall:
        memories = self._load_json(self.memory_path, {})
        memories[key] = value
        self._save_json(self.memory_path, memories)
        return ToolCall("save_memory", True, f"Saved memory: {key}", {"key": key})

    def load_memory(self, key: str) -> ToolCall:
        memories = self._load_json(self.memory_path, {})
        if key not in memories:
            return ToolCall("load_memory", False, f"Memory not found: {key}")
        return ToolCall("load_memory", True, json.dumps(memories[key]), {"key": key, "value": memories[key]})

    def update_memory(self, key: str, value) -> ToolCall:
        return self.save_memory(key, value)

    def delete_memory(self, key: str) -> ToolCall:
        memories = self._load_json(self.memory_path, {})
        memories.pop(key, None)
        self._save_json(self.memory_path, memories)
        return ToolCall("delete_memory", True, f"Deleted memory: {key}")

    def list_memories(self) -> ToolCall:
        memories = self._load_json(self.memory_path, {})
        return ToolCall("list_memories", True, "\n".join(sorted(memories)) or "No memories.", {"memories": memories})

    def plan_task(self, title: str, steps: list[str]) -> ToolCall:
        if not steps:
            return ToolCall("plan_task", False, "At least one step is required.")
        import uuid

        tasks = self._load_json(self.task_path, {})
        task_id = uuid.uuid4().hex[:12]
        now = self._now()
        tasks[task_id] = {"task_id": task_id, "title": title, "status": "planned", "steps": [{"title": step, "status": "pending"} for step in steps], "created_at": now, "updated_at": now}
        self._save_json(self.task_path, tasks)
        return ToolCall("plan_task", True, f"Planned task {task_id}: {title}", {"task_id": task_id})

    def get_task_status(self, task_id: str) -> ToolCall:
        task = self._load_json(self.task_path, {}).get(task_id)
        if not task:
            return ToolCall("get_task_status", False, f"Task not found: {task_id}")
        return ToolCall("get_task_status", True, json.dumps(task, indent=2), task)

    def execute_step(self, task_id: str, step_index: int, confirm: bool = False) -> ToolCall:
        tasks = self._load_json(self.task_path, {})
        task = tasks.get(task_id)
        if not task:
            return ToolCall("execute_step", False, f"Task not found: {task_id}")
        steps = task.get("steps", [])
        if step_index < 0 or step_index >= len(steps):
            return ToolCall("execute_step", False, "Step index out of range.")
        steps[step_index]["status"] = "in_progress"
        task["status"] = "in_progress"
        task["updated_at"] = self._now()
        self._save_json(self.task_path, tasks)
        return ToolCall("execute_step", True, f"Executing step {step_index}", {"task_id": task_id, "step_index": step_index})

    def mark_step_complete(self, task_id: str, step_index: int, confirm: bool = False) -> ToolCall:
        tasks = self._load_json(self.task_path, {})
        task = tasks.get(task_id)
        if not task:
            return ToolCall("mark_step_complete", False, f"Task not found: {task_id}")
        steps = task.get("steps", [])
        if step_index < 0 or step_index >= len(steps):
            return ToolCall("mark_step_complete", False, "Step index out of range.")
        steps[step_index]["status"] = "completed"
        if all(step.get("status") == "completed" for step in steps):
            task["status"] = "completed"
        task["updated_at"] = self._now()
        self._save_json(self.task_path, tasks)
        return ToolCall("mark_step_complete", True, f"Completed step {step_index}", {"task_id": task_id, "step_index": step_index})

    def retry_step(self, task_id: str, step_index: int) -> ToolCall:
        tasks = self._load_json(self.task_path, {})
        task = tasks.get(task_id)
        if not task or step_index >= len(task.get("steps", [])):
            return ToolCall("retry_step", False, "Step index out of range.")
        task["steps"][step_index]["status"] = "pending"
        self._save_json(self.task_path, tasks)
        return ToolCall("retry_step", True, f"Retried step {step_index}")

    def abort_task(self, task_id: str) -> ToolCall:
        tasks = self._load_json(self.task_path, {})
        if task_id not in tasks:
            return ToolCall("abort_task", False, f"Task not found: {task_id}")
        tasks[task_id]["status"] = "aborted"
        self._save_json(self.task_path, tasks)
        return ToolCall("abort_task", True, f"Aborted task {task_id}")

    def task_checkpoint(self, task_id: str, note: str) -> ToolCall:
        checkpoints = self._load_json(self.checkpoint_path, {})
        checkpoints[task_id] = {"note": note, "created_at": self._now()}
        self._save_json(self.checkpoint_path, checkpoints)
        return ToolCall("task_checkpoint", True, f"Checkpoint saved for {task_id}")

    def load_checkpoint(self, task_id: str) -> ToolCall:
        checkpoint = self._load_json(self.checkpoint_path, {}).get(task_id)
        if not checkpoint:
            return ToolCall("load_checkpoint", False, f"No checkpoint for {task_id}")
        return ToolCall("load_checkpoint", True, json.dumps(checkpoint), checkpoint)

    def log_event(self, event_type: str, payload: dict | None = None) -> ToolCall:
        self.config.journal_path.parent.mkdir(parents=True, exist_ok=True)
        record = {"type": event_type, "payload": payload or {}, "created_at": self._now()}
        with self.config.journal_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return ToolCall("log_event", True, event_type, record)

    def replay_session(self) -> ToolCall:
        if not self.config.journal_path.exists():
            return ToolCall("replay_session", True, "No events.", {"events": []})
        lines = [line for line in self.config.journal_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return ToolCall("replay_session", True, "\n".join(lines), {"events": [json.loads(line) for line in lines]})

    def trace_step(self, task_id: str, tool_name: str) -> ToolCall:
        return self.log_event("trace_step", {"task_id": task_id, "tool_name": tool_name})

    def record_tool_latency(self, tool_name: str, latency_ms: int) -> ToolCall:
        return self.log_event("tool_latency", {"tool_name": tool_name, "latency_ms": latency_ms})

    def record_error(self, error: str, context: dict | None = None) -> ToolCall:
        return self.log_event("error", {"error": error, "context": context or {}})

    def summarize_session(self) -> ToolCall:
        replay = self.replay_session()
        return ToolCall("summarize_session", True, f"Session has {len((replay.data or {}).get('events', []))} events.")

    def summarize_run(self) -> ToolCall:
        return self.summarize_session()

    def request_user_approval(self, action: str, confirm: bool = False) -> ToolCall:
        return ToolCall("request_user_approval", confirm, "Approved." if confirm else "Approval required.")

    def check_permission(self, action: str, risky: bool = False, confirm: bool = False) -> ToolCall:
        ok = (not risky) or confirm
        return ToolCall("check_permission", ok, "Permission granted." if ok else "Permission denied; confirmation required.")

    def log_sensitive_action(self, action: str, details: dict | None = None) -> ToolCall:
        return self.log_event("sensitive_action", {"action": action, "details": details or {}})

    def sandbox_shell_execution(self, command: str, confirm: bool = False) -> ToolCall:
        return self.shell_command(command, confirm=confirm)

    def safe_shell_command(self, command: str) -> ToolCall:
        if any(token in command for token in ("&&", ";", "|", "`", "$(`")):
            return ToolCall("safe_shell_command", False, "Unsafe shell composition rejected.")
        call = self.shell_command(command, confirm=True)
        call.tool_name = "safe_shell_command"
        return call

    def process_list(self) -> ToolCall:
        return self.safe_shell_command("ps -eo pid,comm --no-headers")

    def kill_process(self, pid: int, confirm: bool = False) -> ToolCall:
        if not confirm:
            return ToolCall("kill_process", False, "Confirmation required.")
        return self.shell_command(f"kill {int(pid)}", confirm=True)

    def system_info(self) -> ToolCall:
        import platform

        data = {"system": platform.system(), "release": platform.release(), "machine": platform.machine()}
        return ToolCall("system_info", True, json.dumps(data, sort_keys=True), data)

    def env_vars(self, prefix: str = "") -> ToolCall:
        import os

        rows = [f"{key}={value}" for key, value in sorted(os.environ.items()) if not prefix or key.startswith(prefix)]
        return ToolCall("env_vars", True, "\n".join(rows[:100]), {"count": len(rows)})

    def execute_script(self, path: str) -> ToolCall:
        return self.shell_command(f"python {path}", confirm=True)

    def run_tests(self, command: str = "pytest tests/") -> ToolCall:
        return self.shell_command(command, confirm=True)

    def lint_code(self, command: str) -> ToolCall:
        return self.shell_command(command, confirm=True)

    def format_code(self, command: str) -> ToolCall:
        return self.shell_command(command, confirm=True)

    def build_project(self, command: str) -> ToolCall:
        return self.shell_command(command, confirm=True)

    def install_dependencies(self, command: str) -> ToolCall:
        return self.shell_command(command, confirm=True)

    def _git(self, args: list[str]) -> ToolCall:
        completed = subprocess.run(["git", *args], cwd=self.config.workspace_root, capture_output=True, text=True, check=False, timeout=self.config.shell_policy.timeout_seconds)
        output = completed.stdout.strip() or completed.stderr.strip() or "[no output]"
        return ToolCall("git_" + (args[0] if args else "command"), completed.returncode == 0, output, {"returncode": completed.returncode})

    def git_status(self) -> ToolCall:
        return self._git(["status", "--short"])

    def git_diff(self) -> ToolCall:
        return self._git(["diff"])

    def git_log(self) -> ToolCall:
        return self._git(["log", "--oneline", "-5"])

    def git_add(self, paths: list[str]) -> ToolCall:
        return self._git(["add", *paths])

    def git_commit(self, message: str) -> ToolCall:
        return self._git(["commit", "-m", message])

    def git_checkout(self, branch: str) -> ToolCall:
        return self._git(["checkout", branch])

    def git_branch(self, branch: str, create: bool = False) -> ToolCall:
        return self._git(["checkout", "-b", branch] if create else ["branch", branch])

    def git_merge(self, branch: str) -> ToolCall:
        return self._git(["merge", branch])

    def git_reset(self, confirm: bool = False) -> ToolCall:
        if not confirm:
            return ToolCall("git_reset", False, "Confirmation required for git reset.")
        return self._git(["reset", "--hard", "HEAD~1"])

    def git_stash(self) -> ToolCall:
        return self._git(["stash", "push", "-m", "tooling-showcase stash"])

    def fetch_url(self, url: str, confirm: bool = False) -> ToolCall:
        try:
            with urlopen(Request(url, headers={"User-Agent": "tooling-showcase/0.1"}), timeout=20) as response:
                text = response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            return ToolCall("fetch_url", False, f"Fetch failed: {exc}", {"url": url})
        return ToolCall("fetch_url", True, text[:12000], {"url": url})

    def extract_webpage_content(self, url: str | None = None, query: str | None = None) -> ToolCall:
        if not url:
            return ToolCall("extract_webpage_content", False, "URL is required.")
        fetched = self.fetch_url(url)
        if not fetched.ok:
            return fetched
        return ToolCall("extract_webpage_content", True, self._extract_text_from_html(fetched.summary, query=query), {"url": url})

    def parse_json_api(self, url: str, confirm: bool = False) -> ToolCall:
        fetched = self.fetch_url(url, confirm=confirm)
        if not fetched.ok:
            return fetched
        try:
            data = json.loads(fetched.summary)
        except json.JSONDecodeError as exc:
            return ToolCall("parse_json_api", False, f"Invalid JSON: {exc}")
        return ToolCall("parse_json_api", True, "json ok", data)

    def download_file(self, url: str, destination: str) -> ToolCall:
        fetched = self.fetch_url(url)
        if not fetched.ok:
            return fetched
        return self.write_file(destination, fetched.summary)

    def parse_pdf(self, path: str | None = None) -> ToolCall:
        return ToolCall("parse_pdf", False, "PDF parsing is not available in the stdlib runtime." if not path else "PDF parsing is not available.")

    def screenshot_page(self, url: str | None = None) -> ToolCall:
        return ToolCall("screenshot_page", False, "Screenshot capture is not available in the stdlib runtime.")

    def web_search(self, query: str, confirm: bool = False) -> ToolCall:
        api_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_redirect=1&no_html=1"
        api = self.fetch_url(api_url, confirm=confirm)
        if api.ok:
            try:
                payload = json.loads(api.summary)
            except json.JSONDecodeError:
                payload = {}
            lines = []
            if payload.get("AbstractText"):
                lines.append(str(payload["AbstractText"]))
            for topic in payload.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    lines.append(str(topic["Text"]))
            if lines:
                return ToolCall("web_search", True, "\n".join(lines), {"query": query, "results": payload.get("RelatedTopics", [])})

        html_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        html = self.fetch_url(html_url, confirm=confirm)
        if not html.ok:
            return ToolCall("web_search", False, html.summary)
        parser = _DuckDuckGoParser()
        parser.feed(html.summary)
        ranked = self._rank_search_results(query, parser.results[:8])
        rows = [f"- {item.get('title', '')}\n  {item.get('url', '')}" for item in ranked[:5]]
        return ToolCall("web_search", True, "\n".join(rows) if rows else "No results parsed.", {"query": query, "results": ranked[:5], "count": len(ranked[:5])})

    def _rank_search_results(self, query: str, results: list[dict]) -> list[dict]:
        query_lower = query.lower()
        official_hosts = ("kernel.org", "docs.python.org", "github.com", "aylur.github.io", "wiki.archlinux.org")

        def score(item: dict) -> int:
            url = str(item.get("url", "")).lower()
            title = str(item.get("title", "")).lower()
            snippet = str(item.get("snippet", "")).lower()
            value = 0
            if any(host in url for host in official_hosts):
                value += 100
            for term in query_lower.split():
                if term in title:
                    value += 4
                if term in snippet:
                    value += 2
                if term in url:
                    value += 1
            if "official" in query_lower and any(host in url for host in official_hosts):
                value += 20
            return value

        return sorted(results, key=score, reverse=True)

    def _web_search_query_for_context(self, query: str) -> str:
        lowered = query.lower()
        if any(token in lowered for token in ("latest", "current", "today")) and " on " not in lowered:
            return f"{query} as of {self._now()[:10]}"
        return query

    def expand_search_results(self, query: str, limit: int = 3) -> ToolCall:
        search = self.web_search(query)
        if not search.ok:
            return search
        results = (search.data or {}).get("results", [])[:limit]
        chunks = []
        for item in results:
            title = item.get("title") or item.get("Text") or "result"
            url = item.get("url") or item.get("FirstURL") or ""
            if url:
                expanded = self.expand_search_result(url, query=query)
                chunks.append(f"{title}\n{expanded.summary if expanded.ok else expanded.summary}")
            else:
                chunks.append(str(title))
        return ToolCall("expand_search_results", True, "\n\n".join(chunks), {"results": results})

    def weather_lookup(self, query: str) -> ToolCall:
        location = query.split(" in ")[-1].split(" tonight")[0].strip() or query
        geo = self.parse_json_api(f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(location)}&count=1")
        if not geo.ok or not (geo.data or {}).get("results"):
            return ToolCall("weather_lookup", False, f"Location not found: {location}")
        place = geo.data["results"][0]
        weather = self.parse_json_api(f"https://api.open-meteo.com/v1/forecast?latitude={place['latitude']}&longitude={place['longitude']}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m&hourly=temperature_2m,apparent_temperature,weather_code,precipitation_probability,wind_speed_10m&timezone={quote_plus(place.get('timezone', 'auto'))}")
        if not weather.ok:
            return weather
        current = (weather.data or {}).get("current", {})
        name = f"{place.get('name')}, {place.get('country')}"
        return ToolCall("weather_lookup", True, f"Weather for {name}: {current.get('temperature_2m')}C, feels like {current.get('apparent_temperature')}C, wind {current.get('wind_speed_10m')}", {"place": place, "weather": weather.data})

    def latest_linux_kernel(self) -> ToolCall:
        data = self.parse_json_api("https://www.kernel.org/releases.json")
        if not data.ok:
            return data
        releases = (data.data or {}).get("releases", [])
        stable = next((item for item in releases if item.get("moniker") == "stable"), None)
        if not stable:
            return ToolCall("latest_linux_kernel", False, "No stable release found.", data.data)
        return ToolCall("latest_linux_kernel", True, f"Stable: {stable.get('version')} ({stable.get('released', {}).get('isodate', 'unknown date')})", stable)

    def calculate(self, expression: str) -> ToolCall:
        import ast
        import operator

        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def evaluate(node):
            if isinstance(node, ast.Expression):
                return evaluate(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.BinOp) and type(node.op) in operators:
                return operators[type(node.op)](evaluate(node.left), evaluate(node.right))
            if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
                return operators[type(node.op)](evaluate(node.operand))
            raise ValueError("Only numeric arithmetic expressions are supported.")

        try:
            value = evaluate(ast.parse(expression, mode="eval"))
        except Exception as exc:
            return ToolCall("calculate", False, f"Calculation failed: {exc}")
        return ToolCall("calculate", True, str(float(value)) if isinstance(value, (int, float)) else str(value))

    def datetime_now(self) -> ToolCall:
        return ToolCall("datetime_now", True, self._now())

    def draft_system_prompt(
        self,
        title: str = "",
        short_message: str = "",
        context: str = "",
        goal: str = "",
        profile: dict | None = None,
    ) -> ToolCall:
        title = title.strip() or "New system prompt"
        short_message = short_message.strip() or "Reusable assistant behavior"
        context = context.strip()
        goal = goal.strip() or short_message
        profile = profile or {}
        profile_hint = ""
        if isinstance(profile, dict):
            name = str(profile.get("name") or profile.get("nickname") or "").strip()
            prefs = str(profile.get("preferences") or "").strip()
            profile_hint = "\n".join(part for part in (f"User: {name}" if name else "", f"Preferences: {prefs}" if prefs else "") if part)

        full_prompt = "\n".join(
            part
            for part in (
                f"You are configured for: {goal}.",
                "Be direct, practical, and precise. Prefer small correct steps over broad guesses.",
                "Use tools when they improve correctness, and clearly distinguish verified facts from assumptions.",
                context and f"Standing context:\n{context}",
                profile_hint and f"User profile context:\n{profile_hint}",
            )
            if part
        )
        payload = {
            "title": title,
            "short_message": short_message,
            "context": context,
            "full_prompt": full_prompt,
        }
        return ToolCall("draft_system_prompt", True, json.dumps(payload, indent=2), payload)

    def convert_units(self, value: float, from_unit: str, to_unit: str) -> ToolCall:
        factors = {"m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001}
        if from_unit not in factors or to_unit not in factors:
            return ToolCall("convert_units", False, "Unsupported unit.")
        return ToolCall("convert_units", True, str(float(value) * factors[from_unit] / factors[to_unit]))

    def generate_uuid(self) -> ToolCall:
        import uuid

        return ToolCall("generate_uuid", True, str(uuid.uuid4()))

    def encode_decode(self, mode: str, text: str) -> ToolCall:
        import base64

        if mode == "encode":
            return ToolCall("encode_decode", True, base64.b64encode(text.encode()).decode())
        if mode == "decode":
            return ToolCall("encode_decode", True, base64.b64decode(text.encode()).decode())
        return ToolCall("encode_decode", False, "Mode must be encode or decode.")

    def run_model(self, prompt: str = "") -> ToolCall:
        return ToolCall("run_model", False, "Direct model execution is handled by ShowcaseService.")

    def transcribe_audio(self, path: str | None = None) -> ToolCall:
        return ToolCall("transcribe_audio", False, "Audio transcription is not configured.")

    def text_to_speech(self, text: str = "") -> ToolCall:
        return ToolCall("text_to_speech", False, "Text-to-speech is not configured.")

    def analyze_image(self, path: str) -> ToolCall:
        target = self._workspace_path(path)
        if target is None or not target.exists():
            return ToolCall("analyze_image", False, f"Image not found: {path}")
        data = target.read_bytes()
        mime = "image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else "application/octet-stream"
        result = {"path": str(target), "mime_type": mime, "size_bytes": len(data)}
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            import struct

            result["width"], result["height"] = struct.unpack(">II", data[16:24])
        return ToolCall("analyze_image", True, json.dumps(result, sort_keys=True), result)

    def control_device(self, command: str) -> ToolCall:
        self.device_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.device_log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({"command": command, "created_at": self._now()}) + "\n")
        return ToolCall("control_device", True, f"Recorded device command: {command}", {"path": str(self.device_log_path)})
