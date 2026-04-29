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
                "/api/tool",
                "/api/journal/clear",
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

            if clean_path == "/api/ask":
                payload = self._read_json_body()
                text = str(payload.get("text", "")).strip()
                confirm = bool(payload.get("confirm", False))
                model = str(payload.get("model", "")).strip() or None
                system_prompt = str(payload.get("system_prompt", "")).strip() or None
                stream = bool(payload.get("stream", False))
                options = payload.get("options") if isinstance(payload.get("options"), dict) else None
                response_format = payload.get("response_format") or payload.get("format")

                result = _call_service_handle(
                    service,
                    text,
                    confirm=confirm,
                    model=model,
                    system_prompt=system_prompt,
                    stream=stream,
                    options=options,
                    response_format=response_format,
                )

                if stream:
                    self._send_stream(
                        _stream_server_chunks(result.ok, result.message, result.tool_calls)
                    )
                    return

                self._send_json(
                    {
                        "ok": result.ok,
                        "message": result.message,
                        "tool_calls": [_tool_call_to_dict(call) for call in result.tool_calls],
                    },
                    status=HTTPStatus.OK if result.ok else HTTPStatus.BAD_GATEWAY,
                )
                return

            if clean_path == "/api/tool":
                payload = self._read_json_body()
                tool_name = str(payload.get("tool") or payload.get("name") or "").strip()
                arguments = payload.get("arguments") or payload.get("args") or {}
                confirm = bool(payload.get("confirm", False))

                if not tool_name:
                    self._send_json({"ok": False, "error": "Missing tool name."}, status=HTTPStatus.BAD_REQUEST)
                    return

                if not isinstance(arguments, dict):
                    self._send_json({"ok": False, "error": "Tool arguments must be a JSON object."}, status=HTTPStatus.BAD_REQUEST)
                    return

                call = service.tools.run_tool(tool_name, arguments, confirm=confirm)
                ok = bool(getattr(call, "ok", False))
                self._send_json(
                    {"ok": ok, "tool_call": _tool_call_to_dict(call)},
                    status=HTTPStatus.OK if ok else HTTPStatus.BAD_GATEWAY,
                )
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
                max_steps = int(payload.get("max_steps", 5))
                confirm = bool(payload.get("confirm", False))

                result = service.run_autonomous(goal, max_steps=max_steps, confirm=confirm)

                if bool(payload.get("stream", False)):
                    self._send_stream(
                        _stream_server_chunks(result.ok, result.message, result.tool_calls)
                    )
                    return

                self._send_json(
                    {
                        "ok": result.ok,
                        "message": result.message,
                        "tool_calls": [_tool_call_to_dict(call) for call in result.tool_calls],
                    },
                    status=HTTPStatus.OK if result.ok else HTTPStatus.BAD_GATEWAY,
                )
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
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_stream(self, payloads: list[dict]) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            for payload in payloads:
                data = json.dumps(payload).encode("utf-8") + b"\n"
                self.wfile.write(data)

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
    response_format,
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
        }
        for key, value in optional.items():
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


def _load_ollama_models(service: ShowcaseService) -> dict:
    tags_url = _ollama_tags_url(service.config.ollama.endpoint)
    request = Request(tags_url, method="GET")

    try:
        with urlopen(request, timeout=10) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "models": [], "error": f"Ollama HTTP {exc.code}: {body}", "endpoint": tags_url}
    except URLError as exc:
        return {"ok": False, "models": [], "error": f"Failed to reach Ollama: {exc}", "endpoint": tags_url}
    except json.JSONDecodeError as exc:
        return {"ok": False, "models": [], "error": f"Invalid Ollama model JSON: {exc}", "endpoint": tags_url}

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
            }
        )

    models.sort(key=lambda item: item["name"].lower())
    return {"ok": True, "models": models, "endpoint": tags_url}


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


def _stream_server_chunks(ok: bool, message: str, tool_calls: list) -> list[dict]:
    chunks = []

    if "<think>" in message:
        mode = "thinking"
        buffer = message
        while buffer:
            if mode == "thinking":
                start = buffer.find("<think>")
                if start == -1:
                    chunks.append({"type": "content_delta", "delta": buffer})
                    break
                if start > 0:
                    chunks.append({"type": "content_delta", "delta": buffer[:start]})
                buffer = buffer[start + len("<think>"):]
                mode = "content"
            else:
                end = buffer.find("</think>")
                if end == -1:
                    chunks.append({"type": "thinking_delta", "delta": buffer})
                    break
                if end > 0:
                    chunks.append({"type": "thinking_delta", "delta": buffer[:end]})
                buffer = buffer[end + len("</think>"):]
                mode = "thinking"
    else:
        chunks.append({"type": "content_delta", "delta": message})

    chunks.append(
        {
            "type": "final",
            "ok": ok,
            "message": message,
            "tool_calls": [_tool_call_to_dict(call) for call in tool_calls],
            "done": True,
        }
    )
    return chunks


def _safe_int(value, default: int, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


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
