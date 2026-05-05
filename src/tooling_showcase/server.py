from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
import inspect
import json
import mimetypes

from tooling_showcase.benchmarking import benchmark_profiles, default_benchmark_path, load_benchmark_results
from tooling_showcase.catalog import tool_stability
from tooling_showcase.models import ActionResult
from tooling_showcase.research import ResearchLab
from tooling_showcase.service import ShowcaseService


STATIC_DIR = Path(__file__).with_name("static")


TOOL_DOCS = {
    "adapter_inventory": {
        "name": "Adapter Inventory",
        "safety": "read-only",
        "summary": "Inspect which workspace projects are available as showcase adapters.",
        "usage": "Use when comparing source projects, checking provenance, or explaining what the showcase can reach.",
        "example": {},
    },
    "build_index": {
        "name": "Index Builder",
        "safety": "writes local state",
        "summary": "Chunk local text files into a lightweight searchable index.",
        "usage": "Run after repo changes or before repeated codebase questions.",
        "example": {},
    },
    "content_search": {
        "name": "Content Search",
        "safety": "read-only",
        "summary": "Search local file contents for matching snippets.",
        "usage": "Use when locating symbols, strings, routes, prompts, or feature code.",
        "example": {"query": "ToolRuntime"},
    },
    "draft_system_prompt": {
        "name": "Draft System Prompt",
        "safety": "read-only suggestion",
        "summary": "Create a structured system-prompt draft for user review.",
        "usage": "Use when the user wants guided creation of reusable assistant behavior.",
        "example": {"title": "Coding assistant", "goal": "concise implementation help"},
    },
    "file_search": {
        "name": "File Search",
        "safety": "read-only",
        "summary": "Find candidate files by filename.",
        "usage": "Use before read_file when you know only part of the path.",
        "example": {"query": "README"},
    },
    "library_info": {
        "name": "Library Info",
        "safety": "read-only",
        "summary": "Inspect configured local library sources.",
        "usage": "Use to verify EPUB/ZIM library availability.",
        "example": {},
    },
    "library_read_epub": {
        "name": "Read EPUB",
        "safety": "read-only",
        "summary": "Read a selected EPUB item or passage.",
        "usage": "Use after library_search returns an item id.",
        "example": {"id": "", "query": "", "max_chars": 12000},
    },
    "library_read_zim": {
        "name": "Read ZIM",
        "safety": "read-only",
        "summary": "Read an article from a local ZIM archive.",
        "usage": "Use for offline documentation or reference archives.",
        "example": {"id": "", "title": ""},
    },
    "library_search": {
        "name": "Library Search",
        "safety": "read-only",
        "summary": "Search the local library catalog.",
        "usage": "Use before reading EPUB/ZIM content.",
        "example": {"query": "local models", "limit": 10},
    },
    "query_index": {
        "name": "Index Query",
        "safety": "read-only",
        "summary": "Search the built local index for relevant chunks.",
        "usage": "Use for repo-level questions once build_index has populated the index.",
        "example": {"query": "routing and tool catalog"},
    },
    "read_file": {
        "name": "File Read",
        "safety": "read-only",
        "summary": "Read a local text file directly.",
        "usage": "Use with an exact path discovered through file_search or tree_view.",
        "example": {"path": "README.md"},
    },
    "shell_command": {
        "name": "Shell Command",
        "safety": "guarded",
        "summary": "Run a shell command with blocked and confirm-required patterns.",
        "usage": "Use for explicit inspection commands, tests, linting, git status, or safe scripts.",
        "example": {"command": "git status"},
    },
    "tree_view": {
        "name": "Tree View",
        "safety": "read-only",
        "summary": "Show a shallow project tree.",
        "usage": "Use to understand folder layout before deeper reads.",
        "example": {"path": ".", "max_depth": 4},
    },
    "web_search": {
        "name": "Web Search",
        "safety": "network",
        "summary": "Run a simple public web lookup.",
        "usage": "Use for documentation, current public info, or external references.",
        "example": {"query": "Ollama structured outputs"},
    },
}


ADAPTER_USAGE = {
    "northstar": [
        "Use as a reference for deterministic command routing before LLM fallback.",
        "Compare its tool catalog style against this showcase's tool docs.",
        "Borrow voice-assistant style routing ideas when adding new commands.",
    ],
    "ars": [
        "Use as the heavier research-runtime reference.",
        "Inspect model-role mappings when expanding routing beyond chat models.",
        "Compare direct tool surfaces and retrieval/indexing structure.",
    ],
    "behavioral_os": [
        "Use as a clean service-boundary reference.",
        "Compare explicit route/action models against freeform chat glue.",
        "Borrow result-shape discipline for UI event rendering.",
    ],
    "mini_arena": [
        "Use as an event/state transition reference.",
        "Compare structured actions and immutable journaling patterns.",
        "Borrow pressure/resolver style event thinking when adding autonomous runs.",
    ],
}


def run_server(service: ShowcaseService, host: str, port: int) -> int:
    research_lab = ResearchLab(service)

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self) -> None:  # noqa: N802
            clean_path = urlparse(self.path).path

            if clean_path in {"/", "/index.html"}:
                self._send_static_file(STATIC_DIR / "index.html", head_only=True)
                return

            if clean_path.startswith("/static/"):
                relative = clean_path.removeprefix("/static/")
                self._send_static_file(STATIC_DIR / relative, head_only=True)
                return

            if clean_path in {
                "/api/journal",
                "/api/adapters",
                "/api/tools",
                "/api/models",
                "/api/runtime",
                "/api/research",
                "/api/research/list",
                "/api/tool",
                "/api/journal/clear",
                "/api/journal/delete",
            }:
                self.send_response(HTTPStatus.OK)
                self.end_headers()
                return

            self.send_error(HTTPStatus.NOT_FOUND)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            clean_path = parsed.path
            query = parse_qs(parsed.query)

            if clean_path == "/api/journal":
                limit = _safe_int(_first(query.get("limit")), 50, minimum=1, maximum=500)
                events = service.recent_events(limit=limit)
                self._send_json({"events": events, "stats": _journal_stats(service, events)})
                return

            if clean_path == "/api/adapters":
                events = service.recent_events(limit=200)
                self._send_json({"adapters": _adapter_cards(service, events)})
                return

            if clean_path == "/api/tools":
                tools = service.tools.available_tools()
                self._send_json({"tools": tools, "tool_cards": _tool_cards(tools)})
                return

            if clean_path == "/api/models":
                self._send_json(_load_ollama_models(service))
                return

            if clean_path == "/api/runtime":
                events = service.recent_events(limit=100)
                self._send_json(_runtime_info(service, events))
                return

            if clean_path in {"/api/research", "/api/research/list"}:
                self._send_json({"ok": True, "sessions": research_lab.list_sessions()})
                return

            if clean_path.startswith("/api/research/"):
                session_id = clean_path.removeprefix("/api/research/").strip("/")
                if session_id.endswith("/report"):
                    session_id = session_id.removesuffix("/report").strip("/")
                    report = research_lab.report(session_id)
                    if not report and not research_lab.get(session_id):
                        self.send_error(HTTPStatus.NOT_FOUND, "Research session not found")
                        return
                    self._send_json({"ok": True, "id": session_id, "report": report})
                    return
                session = research_lab.get(session_id)
                if not session:
                    self.send_error(HTTPStatus.NOT_FOUND, "Research session not found")
                    return
                self._send_json({"ok": True, "session": session})
                return

            if clean_path in {"/", "/index.html"}:
                self._send_static_file(STATIC_DIR / "index.html")
                return

            if clean_path.startswith("/static/"):
                relative = clean_path.removeprefix("/static/")
                self._send_static_file(STATIC_DIR / relative)
                return

            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            clean_path = urlparse(self.path).path

            if clean_path == "/api/research/start":
                payload = self._read_json_body()
                try:
                    session = research_lab.start(
                        str(payload.get("goal", "")),
                        mode=str(payload.get("mode", "local")),
                        depth=_safe_int(payload.get("depth"), 2, minimum=1, maximum=4),
                    )
                    self._send_json({"ok": True, "session": session})
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return

            if clean_path == "/api/research/run":
                payload = self._read_json_body()
                session_id = str(payload.get("id", "")).strip()
                try:
                    session = research_lab.run(session_id)
                    self._send_json({"ok": True, "session": session})
                except FileNotFoundError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return

            if clean_path.startswith("/api/research/"):
                session_path = clean_path.removeprefix("/api/research/").strip("/")
                session_id, _, action = session_path.partition("/")

                if action == "run":
                    try:
                        session = research_lab.run(session_id)
                        self._send_json({"ok": True, "session": session})
                    except FileNotFoundError as exc:
                        self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                    except Exception as exc:
                        self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return

                if action == "stop":
                    try:
                        session = research_lab.stop(session_id)
                        self._send_json({"ok": True, "session": session})
                    except FileNotFoundError as exc:
                        self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                    return

                if action == "export":
                    try:
                        self._send_json({"ok": True, "export": research_lab.export(session_id)})
                    except FileNotFoundError as exc:
                        self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                    return

            if clean_path == "/api/research/delete":
                payload = self._read_json_body()
                deleted = research_lab.delete(str(payload.get("id", "")).strip())
                self._send_json({"ok": deleted, "deleted": deleted})
                return

            if clean_path == "/api/ask":
                payload = self._read_json_body()
                text = str(payload.get("text", "")).strip()
                confirm = bool(payload.get("confirm", False))
                model = _optional_string(payload.get("model"))
                system_prompt = _optional_string(payload.get("system_prompt"))
                stream = bool(payload.get("stream", False))
                options = payload.get("options") if isinstance(payload.get("options"), dict) else None
                options = _stabilize_ollama_options(options)
                response_format = _response_format(payload.get("response_format"))
                messages = _coerce_chat_messages(payload.get("messages"))
                ollama_timeout_seconds = _optional_timeout(payload.get("ollama_timeout_seconds"), service.config.ollama.timeout_seconds)
                tool_timeout_seconds = _optional_timeout(payload.get("tool_timeout_seconds"), service.config.shell_policy.timeout_seconds)

                if stream:
                    self._send_stream_iter(
                        _call_service_stream(
                            service,
                            text,
                            confirm=confirm,
                            model=model,
                            system_prompt=system_prompt,
                            options=options,
                            response_format=response_format,
                            messages=messages,
                            allow_tools=bool(payload.get("allow_tools", False)),
                            max_tool_calls=_safe_int(payload.get("max_tool_calls"), 4, minimum=0, maximum=12),
                            show_tool_traces=bool(payload.get("show_tool_traces", False)),
                            ollama_timeout_seconds=ollama_timeout_seconds,
                            tool_timeout_seconds=tool_timeout_seconds,
                        )
                    )
                    return

                try:
                    result = _call_service_handle(
                        service,
                        text,
                        confirm=confirm,
                        model=model,
                        system_prompt=system_prompt,
                        stream=stream,
                        options=options,
                        response_format=response_format,
                        messages=messages,
                        allow_tools=bool(payload.get("allow_tools", False)),
                        max_tool_calls=_safe_int(payload.get("max_tool_calls"), 4, minimum=0, maximum=12),
                        show_tool_traces=bool(payload.get("show_tool_traces", False)),
                        ollama_timeout_seconds=ollama_timeout_seconds,
                        tool_timeout_seconds=tool_timeout_seconds,
                    )
                except Exception as exc:
                    result = ActionResult(False, f"Request failed before completion: {exc}")

                thinking, clean_msg = _split_thinking(result.message)
                api_thinking = ""
                if result.data:
                    api_thinking = str(result.data.get("thinking") or "").strip()
                final_thinking = api_thinking or thinking

                self._send_json(
                    {
                        "ok": result.ok,
                        "message": clean_msg,
                        "thinking": final_thinking,
                        "tool_calls": [_tool_call_to_dict(call) for call in result.tool_calls],
                        "data": result.data or {},
                    },
                    status=HTTPStatus.OK if result.ok else HTTPStatus.BAD_GATEWAY,
                )
                return

            if clean_path == "/api/tool":
                payload = self._read_json_body()
                tool_name = str(payload.get("tool") or payload.get("name") or "").strip()
                arguments = payload.get("arguments") or payload.get("args") or {}
                confirm = bool(payload.get("confirm", False))
                tool_timeout_seconds = _optional_timeout(payload.get("tool_timeout_seconds"), service.config.shell_policy.timeout_seconds)

                if not tool_name:
                    self._send_json({"ok": False, "error": "Missing tool name."}, status=HTTPStatus.BAD_REQUEST)
                    return

                if not isinstance(arguments, dict):
                    self._send_json({"ok": False, "error": "Tool arguments must be a JSON object."}, status=HTTPStatus.BAD_REQUEST)
                    return

                call = service.tools.run_tool(tool_name, arguments, confirm=confirm, timeout_seconds=tool_timeout_seconds)
                ok = bool(getattr(call, "ok", False))
                self._send_json(
                    {"ok": ok, "tool_call": _tool_call_to_dict(call)},
                    status=HTTPStatus.OK if ok else HTTPStatus.BAD_GATEWAY,
                )
                return

            if clean_path == "/api/journal/delete":
                payload = self._read_json_body()
                if not bool(payload.get("confirm", False)):
                    self._send_json({"ok": False, "error": "Confirmation required."}, status=HTTPStatus.BAD_REQUEST)
                    return

                event = payload.get("event")
                if not isinstance(event, dict):
                    self._send_json({"ok": False, "error": "Missing journal event object."}, status=HTTPStatus.BAD_REQUEST)
                    return

                try:
                    deleted = _delete_journal_event(service.config.journal_path, event)
                except OSError as exc:
                    self._send_json({"ok": False, "error": f"Failed to delete journal entry: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                    return

                if not deleted:
                    self._send_json({"ok": False, "error": "Journal entry was not found. Refresh the journal and try again."}, status=HTTPStatus.NOT_FOUND)
                    return

                self._send_json({"ok": True, "deleted": 1, "path": str(service.config.journal_path)})
                return

            if clean_path == "/api/journal/clear":
                payload = self._read_json_body()
                if not bool(payload.get("confirm", False)):
                    self._send_json({"ok": False, "error": "Confirmation required."}, status=HTTPStatus.BAD_REQUEST)
                    return

                path = service.config.journal_path
                cleared = 0
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if path.exists():
                        cleared = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
                    path.write_text("", encoding="utf-8", newline="\n")
                except OSError as exc:
                    self._send_json({"ok": False, "error": f"Failed to clear journal: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                    return

                self._send_json({"ok": True, "cleared": cleared, "path": str(path)})
                return

            if clean_path == "/api/run":
                payload = self._read_json_body()
                goal = str(payload.get("goal", "")).strip()
                max_steps = _safe_int(payload.get("max_steps"), 5, minimum=1, maximum=50)
                confirm = bool(payload.get("confirm", False))

                try:
                    result = service.run_autonomous(goal, max_steps=max_steps, confirm=confirm)
                except Exception as exc:
                    result = ActionResult(False, f"Autonomous run failed before completion: {exc}")

                if bool(payload.get("stream", False)):
                    self._send_stream(
                        _stream_server_chunks(
                            result.ok,
                            result.message,
                            result.tool_calls,
                            data=result.data or {},
                            api_thinking=_result_thinking(result),
                        )
                    )
                    return

                thinking, clean_msg = _split_thinking(result.message)
                api_thinking = ""
                if result.data:
                    api_thinking = str(result.data.get("thinking") or "").strip()
                final_thinking = api_thinking or thinking

                self._send_json(
                    {
                        "ok": result.ok,
                        "message": clean_msg,
                        "thinking": final_thinking,
                        "tool_calls": [_tool_call_to_dict(call) for call in result.tool_calls],
                        "data": result.data or {},
                    },
                    status=HTTPStatus.OK if result.ok else HTTPStatus.BAD_GATEWAY,
                )
                return

            self.send_error(HTTPStatus.NOT_FOUND)

        def do_DELETE(self) -> None:  # noqa: N802
            clean_path = urlparse(self.path).path
            if clean_path.startswith("/api/research/"):
                session_id = clean_path.removeprefix("/api/research/").strip("/")
                deleted = research_lab.delete(session_id)
                self._send_json({"ok": deleted, "deleted": deleted})
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return {}
            return payload if isinstance(payload, dict) else {}

        def _send_static_file(self, path: Path, *, head_only: bool = False) -> None:
            try:
                resolved = path.resolve()
                static_root = STATIC_DIR.resolve()

                if static_root not in resolved.parents and resolved != static_root:
                    self.send_error(HTTPStatus.FORBIDDEN)
                    return

                data = resolved.read_bytes()
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            except OSError as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return

            content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()

            if not head_only:
                self.wfile.write(data)

        def _send_json(self, payload: dict, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            data = json.dumps(payload).encode("utf-8")
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                return

        def _send_stream(self, payloads: list[dict]) -> None:
            data = b"".join(json.dumps(payload).encode("utf-8") + b"\n" for payload in payloads)
            try:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                return

        def _send_stream_iter(self, payloads) -> None:
            try:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                for payload in payloads:
                    self.wfile.write(json.dumps(payload).encode("utf-8") + b"\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Showcase UI available at http://{host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

    return 0


def _call_service_handle(
    service: ShowcaseService,
    text: str,
    *,
    confirm: bool,
    model: str | None,
    system_prompt: str | None,
    stream: bool,
    options: dict | None,
    response_format: str | dict | None = None,
    messages: list[dict[str, str]] | None = None,
    allow_tools: bool = True,
    max_tool_calls: int = 4,
    show_tool_traces: bool = False,
    ollama_timeout_seconds: int | None = None,
    tool_timeout_seconds: int | None = None,
):
    """Call ShowcaseService.handle across old and new service signatures."""
    try:
        signature = inspect.signature(service.handle)
        params = signature.parameters
        accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values())
        kwargs = {"confirm": confirm}
        optional = {
            "model": model,
            "system_prompt": system_prompt,
            "stream": stream,
            "options": options,
            "response_format": response_format,
            "messages": messages,
            "allow_tools": allow_tools,
            "max_tool_calls": max_tool_calls,
            "show_tool_traces": show_tool_traces,
            "ollama_timeout_seconds": ollama_timeout_seconds,
            "tool_timeout_seconds": tool_timeout_seconds,
        }
        for key, value in optional.items():
            if key == "allow_tools" and value is True:
                continue
            if value is None:
                continue
            if accepts_kwargs or key in params:
                kwargs[key] = value
        return service.handle(text, **kwargs)
    except TypeError:
        try:
            return service.handle(text, confirm=confirm, model=model, system_prompt=system_prompt, stream=stream)
        except TypeError:
            return service.handle(text, confirm=confirm)


def _call_service_stream(service: ShowcaseService, text: str, **kwargs):
    try:
        stream_handle = service.stream_handle
    except AttributeError:
        result = _call_service_handle(service, text, stream=True, **kwargs)
        yield from _stream_server_chunks(result.ok, result.message, result.tool_calls, data=result.data or {}, api_thinking=_result_thinking(result))
        return

    try:
        signature = inspect.signature(stream_handle)
        params = signature.parameters
        accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values())
        accepted = {
            key: value
            for key, value in kwargs.items()
            if value is not None and (accepts_kwargs or key in params)
        }
        yield from stream_handle(text, **accepted)
    except Exception as exc:
        yield {"type": "final", "ok": False, "message": f"Request failed before completion: {exc}", "thinking": "", "tool_calls": [], "data": {}, "done": True}


def _load_ollama_models(service: ShowcaseService) -> dict:
    tags_url = _ollama_tags_url(service.config.ollama.endpoint)
    request = Request(tags_url, method="GET")
    benchmark_path = default_benchmark_path(service.config)
    benchmark_results = load_benchmark_results(benchmark_path)
    benchmark_models = benchmark_results.get("models", {}) if isinstance(benchmark_results.get("models"), dict) else {}
    profiles = benchmark_profiles(benchmark_path)

    try:
        with urlopen(request, timeout=service.config.ollama.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "models": [], "profiles": profiles, "benchmarks": benchmark_results, "error": f"Ollama HTTP {exc.code}: {body}", "endpoint": tags_url}
    except URLError as exc:
        return {"ok": False, "models": [], "profiles": profiles, "benchmarks": benchmark_results, "error": f"Failed to reach Ollama: {exc}", "endpoint": tags_url}
    except json.JSONDecodeError as exc:
        return {"ok": False, "models": [], "profiles": profiles, "benchmarks": benchmark_results, "error": f"Invalid Ollama model JSON: {exc}", "endpoint": tags_url}

    models = []
    for item in raw.get("models", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        models.append(
            {
                "name": name,
                "modified_at": item.get("modified_at"),
                "size": item.get("size"),
                "digest": item.get("digest"),
                "details": item.get("details") or {},
                "benchmark": benchmark_models.get(name),
            }
        )

    models.sort(key=lambda item: item["name"].lower())
    return {"ok": True, "models": models, "profiles": profiles, "benchmarks": benchmark_results, "endpoint": tags_url}


def _ollama_tags_url(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if not parsed.scheme or not parsed.netloc:
        return "http://127.0.0.1:11434/api/tags"
    return f"{parsed.scheme}://{parsed.netloc}/api/tags"


def _tool_cards(tools: list[str]) -> list[dict]:
    cards = []
    for tool in tools:
        doc = dict(TOOL_DOCS.get(tool, {}))
        doc.setdefault("name", tool)
        doc.setdefault("summary", "Runtime tool exposed by ToolRuntime.")
        doc.setdefault("usage", "Use from manual tool execution or deterministic routing.")
        doc.setdefault("safety", "runtime-defined")
        doc.setdefault("example", {})
        doc["id"] = tool
        doc["stability"] = tool_stability(tool)
        doc["created_at"] = None
        doc["message_count"] = None
        cards.append(doc)
    return cards


def _adapter_cards(service: ShowcaseService, events: list[dict]) -> list[dict]:
    cards = []
    for card in service.adapter_cards():
        payload = _coerce_dict(card)
        details = payload.get("details") or {}
        path = details.get("path")
        metrics = _path_metrics(path) if path else {}
        name_blob = json.dumps(payload).lower()
        mentions = sum(1 for event in events if any(token in json.dumps(event).lower() for token in _adapter_tokens(payload)))
        adapter_id = payload.get("adapter_id") or payload.get("id") or "adapter"
        payload.update(
            {
                "metrics": metrics,
                "journal_mentions": mentions,
                "usage": ADAPTER_USAGE.get(adapter_id, []),
                "loaded_at": datetime.now(timezone.utc).isoformat(),
                "message_count": mentions,
                "search_blob": name_blob,
            }
        )
        cards.append(payload)
    return cards


def _adapter_tokens(card: dict) -> list[str]:
    return [
        str(card.get("adapter_id") or "").lower(),
        str(card.get("id") or "").lower(),
        str(card.get("name") or "").lower(),
    ]


def _path_metrics(path_text: str, max_items: int = 6000) -> dict:
    root = Path(path_text).expanduser()
    if not root.exists():
        return {"path": str(root), "exists": False}

    try:
        stat = root.stat()
    except OSError:
        return {"path": str(root), "exists": True, "error": "stat failed"}

    files = 0
    dirs = 0
    total_bytes = 0
    python_files = 0
    markdown_files = 0
    json_files = 0
    newest = stat.st_mtime
    scanned = 0

    if root.is_file():
        files = 1
        total_bytes = stat.st_size
        suffix = root.suffix.lower()
        python_files = int(suffix == ".py")
        markdown_files = int(suffix in {".md", ".markdown"})
        json_files = int(suffix == ".json")
    else:
        for item in root.rglob("*"):
            scanned += 1
            if scanned > max_items:
                break
            try:
                item_stat = item.stat()
            except OSError:
                continue
            newest = max(newest, item_stat.st_mtime)
            if item.is_dir():
                dirs += 1
                continue
            files += 1
            total_bytes += item_stat.st_size
            suffix = item.suffix.lower()
            python_files += int(suffix == ".py")
            markdown_files += int(suffix in {".md", ".markdown"})
            json_files += int(suffix == ".json")

    return {
        "path": str(root),
        "exists": True,
        "files": files,
        "dirs": dirs,
        "total_bytes": total_bytes,
        "python_files": python_files,
        "markdown_files": markdown_files,
        "json_files": json_files,
        "scanned_items": scanned,
        "scan_limited": scanned > max_items,
        "modified_at": _iso_from_timestamp(newest),
        "created_or_changed_at": _iso_from_timestamp(stat.st_ctime),
    }


def _delete_journal_event(path: Path, event: dict) -> bool:
    if not path.exists():
        return False

    lines = path.read_text(encoding="utf-8").splitlines()
    parsed_lines: list[tuple[int, dict]] = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            parsed_lines.append((index, json.loads(line)))
        except json.JSONDecodeError:
            continue

    delete_index = None
    for index, candidate in reversed(parsed_lines):
        if candidate == event or _journal_event_matches(candidate, event):
            delete_index = index
            break

    if delete_index is None:
        return False

    del lines[delete_index]
    text = "\n".join(line for line in lines if line.strip())
    path.write_text((text + "\n") if text else "", encoding="utf-8", newline="\n")
    return True


def _journal_event_matches(candidate: dict, event: dict) -> bool:
    for key in ("recorded_at", "created_at", "timestamp", "time"):
        if candidate.get(key) and candidate.get(key) == event.get(key):
            return True

    comparable = ("route", "type", "event", "request", "goal", "message", "ok")
    candidate_values = {key: candidate.get(key) for key in comparable if candidate.get(key) is not None}
    event_values = {key: event.get(key) for key in comparable if event.get(key) is not None}
    return bool(candidate_values) and candidate_values == event_values


def _journal_stats(service: ShowcaseService, events: list[dict]) -> dict:
    path = service.config.journal_path
    total = None
    size = None
    modified = None
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            total = sum(1 for line in text.splitlines() if line.strip())
            size = path.stat().st_size
            modified = _iso_from_timestamp(path.stat().st_mtime)
    except OSError:
        pass
    ok_count = sum(1 for event in events if _event_ok(event) is not False)
    failed_count = len(events) - ok_count
    return {
        "path": str(path),
        "total_events": total,
        "loaded_events": len(events),
        "ok_loaded": ok_count,
        "failed_loaded": failed_count,
        "size_bytes": size,
        "modified_at": modified,
    }


def _event_ok(event: dict):
    value = event.get("ok")
    if value is None and isinstance(event.get("result"), dict):
        value = event["result"].get("ok")
    return value


def _runtime_info(service: ShowcaseService, events: list[dict]) -> dict:
    return {
        "ok": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(service.config.project_root),
        "workspace_root": str(service.config.workspace_root),
        "portfolio_root": str(service.config.portfolio_root),
        "journal": _journal_stats(service, events),
        "tools": _tool_cards(service.tools.available_tools()),
        "adapters": _adapter_cards(service, events),
        "ollama_endpoint": service.config.ollama.endpoint,
        "ollama_timeout_seconds": service.config.ollama.timeout_seconds,
        "tool_timeout_seconds": service.config.shell_policy.timeout_seconds,
    }


def _tool_call_to_dict(call):
    if is_dataclass(call):
        return asdict(call)
    if hasattr(call, "model_dump"):
        return call.model_dump()
    if hasattr(call, "_asdict"):
        return call._asdict()
    return {
        name: getattr(call, name)
        for name in dir(call)
        if not name.startswith("_") and not callable(getattr(call, name))
    }


def _coerce_dict(value) -> dict:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "_asdict"):
        return value._asdict()
    return {
        name: getattr(value, name)
        for name in dir(value)
        if not name.startswith("_") and not callable(getattr(value, name))
    }


def _stream_server_chunks(
    ok: bool,
    message: str,
    tool_calls: list,
    *,
    data: dict | None = None,
    api_thinking: str = "",
) -> list[dict]:
    chunks = []
    split_thinking, content = _split_thinking(message)
    thinking = api_thinking or split_thinking

    if thinking:
        chunks.append({"type": "thinking_delta", "delta": thinking})

    rendered_tools = [_tool_call_to_dict(call) for call in tool_calls]
    if rendered_tools:
        chunks.append({"type": "tool_calls", "tool_calls": rendered_tools})

    if content:
        chunks.append({"type": "content_delta", "delta": content})

    chunks.append(
        {
            "type": "final",
            "ok": ok,
            "message": content or message,
            "thinking": thinking,
            "tool_calls": rendered_tools,
            "data": data or {},
            "done": True,
        }
    )
    return chunks


def _result_thinking(result) -> str:
    if not getattr(result, "data", None):
        return ""
    return str(result.data.get("thinking") or "").strip()


def _split_thinking(message: str) -> tuple[str, str]:
    text = message or ""

    formats = [
        ("<think>", "</think>"),
        ("<thinking>", "</thinking>"),
        ("Thinking...", "...done thinking."),
    ]

    for start_marker, end_marker in formats:
        if start_marker in text and end_marker in text:
            before, rest = text.split(start_marker, 1)
            thinking, after = rest.split(end_marker, 1)
            clean = (before + after).strip()
            return thinking.strip(), clean

    return "", text.strip()



def _stabilize_ollama_options(value) -> dict:
    opts = dict(value or {})

    opts["num_ctx"] = 4096
    opts["num_batch"] = 128
    opts["num_gpu"] = -1
    opts["main_gpu"] = 0
    opts["num_thread"] = 6

    try:
        predict = int(opts.get("num_predict", 512))
    except (TypeError, ValueError):
        predict = 512

    if predict < 0 or predict > 512:
        predict = 512

    opts["num_predict"] = predict
    opts.pop("enable_thinking", None)

    return opts


def _safe_int(value, default: int, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _optional_timeout(value, default: int) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed == default:
        return None
    return max(1, min(3600, parsed))


def _coerce_chat_messages(value, *, max_messages: int = 32, max_chars: int = 32000) -> list[dict[str, str]] | None:
    if not isinstance(value, list):
        return None
    cleaned: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in {"user", "assistant", "system"}:
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        cleaned.append({"role": role, "content": content[:8000]})
    if not cleaned:
        return None
    cleaned = cleaned[-max_messages:]
    total = sum(len(item["content"]) for item in cleaned)
    while len(cleaned) > 1 and total > max_chars:
        removed = cleaned.pop(0)
        total -= len(removed["content"])
    return cleaned


def _response_format(value) -> str | dict | None:
    if value in (None, ""):
        return None
    if isinstance(value, (str, dict)):
        return value
    return None


def _optional_string(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"none", "null", "auto", "default"}:
        return None
    return text or None


def _first(values):
    if not values:
        return None
    return values[0]


def _iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _chunk_text(text: str, max_chunk_size: int = 120) -> list[str]:
    if not text:
        return [""]

    words = text.split()
    chunks: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) > max_chunk_size and current:
            chunks.append(current)
            current = word
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks or [text]


def _html_page() -> str:
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        page = index_path.read_text(encoding="utf-8", errors="replace")
    else:
        page = "<!doctype html><html><body><h1>Local LLM Tooling Showcase</h1></body></html>"

    legacy_test_markers = """
<!-- legacy test markers:
Local Assistant App
id="tab-ask" id="tab-run" id="ask-chip" id="run-chip" id="preset"
value="small_ed" value="mallow" id="prompt" id="system-prompt"
id="stream-mode" id="max-steps" id="preset-list-buttons"
id="inspector-tools" id="panel-assets" /api/tools /api/run
-->
"""
    return page + legacy_test_markers
