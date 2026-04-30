from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import inspect
import json

from tooling_showcase.service import ShowcaseService


def run_ollama_wrapper(
    service: ShowcaseService,
    *,
    host: str,
    port: int,
    upstream_endpoint: str,
) -> int:
    upstream_base = _upstream_base(upstream_endpoint)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self._proxy_request()

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/api/chat":
                self._handle_chat()
                return
            if self.path == "/api/generate":
                self._handle_generate()
                return
            self._proxy_request()

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _handle_chat(self) -> None:
            payload = self._read_json_body()
            text = build_service_request_text(payload)
            confirm = bool(payload.get("showcase_confirm", False))
            model = _optional_string(payload.get("model"))
            system_prompt = extract_system_prompt(payload)
            result = _call_showcase_service(
                service,
                text,
                confirm=confirm,
                model=model,
                system_prompt=system_prompt,
                options=payload.get("options") if isinstance(payload.get("options"), dict) else None,
                response_format=_response_format(payload.get("format")),
                allow_tools=bool(payload.get("showcase_allow_tools", True)),
                max_tool_calls=int(payload.get("showcase_max_tool_calls", 4)),
                show_tool_traces=bool(payload.get("showcase_show_tool_traces", False)),
                ollama_timeout_seconds=_optional_timeout(payload.get("showcase_ollama_timeout_seconds"), _service_ollama_timeout(service)),
                tool_timeout_seconds=_optional_timeout(payload.get("showcase_tool_timeout_seconds"), _service_tool_timeout(service)),
            )
            if bool(payload.get("stream", False)):
                self._send_ollama_stream(
                    stream_chat_chunks(payload, result),
                )
                return
            response = build_ollama_chat_response(payload, result)
            self._send_ollama_response(response, stream=False)

        def _handle_generate(self) -> None:
            payload = self._read_json_body()
            text = build_service_request_text(payload)
            confirm = bool(payload.get("showcase_confirm", False))
            model = _optional_string(payload.get("model"))
            system_prompt = extract_system_prompt(payload)
            result = _call_showcase_service(
                service,
                text,
                confirm=confirm,
                model=model,
                system_prompt=system_prompt,
                options=payload.get("options") if isinstance(payload.get("options"), dict) else None,
                response_format=_response_format(payload.get("format")),
                allow_tools=bool(payload.get("showcase_allow_tools", True)),
                max_tool_calls=int(payload.get("showcase_max_tool_calls", 4)),
                show_tool_traces=bool(payload.get("showcase_show_tool_traces", False)),
                ollama_timeout_seconds=_optional_timeout(payload.get("showcase_ollama_timeout_seconds"), _service_ollama_timeout(service)),
                tool_timeout_seconds=_optional_timeout(payload.get("showcase_tool_timeout_seconds"), _service_tool_timeout(service)),
            )
            if bool(payload.get("stream", False)):
                self._send_ollama_stream(
                    stream_generate_chunks(payload, result),
                )
                return
            response = build_ollama_generate_response(payload, result)
            self._send_ollama_response(response, stream=False)

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) or b"{}"
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else {}

        def _send_ollama_response(self, payload: dict, *, stream: bool) -> None:
            data = (json.dumps(payload) + ("\n" if stream else "")).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "Content-Type",
                "application/x-ndjson; charset=utf-8"
                if stream
                else "application/json; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_ollama_stream(self, payloads: list[dict]) -> None:
            data = "".join(json.dumps(payload) + "\n" for payload in payloads).encode(
                "utf-8"
            )
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _proxy_request(self) -> None:
            target = upstream_base + self.path
            body = b""
            if self.command in {"POST", "PUT", "PATCH"}:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
            request = Request(target, data=body or None, method=self.command)
            for key, value in self.headers.items():
                if key.lower() != "host":
                    request.add_header(key, value)
            try:
                with urlopen(request, timeout=_service_ollama_timeout(service)) as response:
                    data = response.read()
                    self.send_response(getattr(response, "status", 200))
                    self.send_header(
                        "Content-Type",
                        response.headers.get(
                            "Content-Type", "application/json; charset=utf-8"
                        ),
                    )
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
            except HTTPError as exc:
                data = exc.read()
                self.send_response(exc.code)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except URLError as exc:
                self.send_error(HTTPStatus.BAD_GATEWAY, str(exc))

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Showcase Ollama wrapper at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _call_showcase_service(service, text: str, **kwargs):
    try:
        signature = inspect.signature(service.handle)
        params = signature.parameters
        accepts_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()
        )
        accepted = {
            key: value
            for key, value in kwargs.items()
            if value is not None and (accepts_kwargs or key in params)
        }
        return service.handle(text, **accepted)
    except TypeError:
        return service.handle(
            text,
            confirm=kwargs.get("confirm", False),
            model=kwargs.get("model"),
            system_prompt=kwargs.get("system_prompt"),
        )


def _response_format(value):
    if value in (None, ""):
        return None
    if isinstance(value, (str, dict)):
        return value
    return None


def _optional_string(value):
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"none", "null", "auto", "default"}:
        return None
    return text or None


def _optional_timeout(value, default: int) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed == default:
        return None
    return max(1, min(3600, parsed))


def _service_ollama_timeout(service) -> int:
    return int(getattr(getattr(getattr(service, "config", None), "ollama", None), "timeout_seconds", 120))


def _service_tool_timeout(service) -> int:
    return int(getattr(getattr(getattr(service, "config", None), "shell_policy", None), "timeout_seconds", 30))


def extract_chat_text(payload: dict) -> str:
    messages = payload.get("messages") or []
    parts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("role") == "user":
            content = str(message.get("content", "")).strip()
            if content:
                parts.append(content)
    if parts:
        return "\n\n".join(parts)
    prompt = str(payload.get("prompt", "")).strip()
    if prompt:
        return prompt
    return ""


def extract_latest_user_text(payload: dict) -> str:
    messages = payload.get("messages") or []
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if message.get("role") != "user":
            continue
        content = str(message.get("content", "")).strip()
        if content:
            return content
    return str(payload.get("prompt", "")).strip()


def build_service_request_text(payload: dict) -> str:
    latest = extract_latest_user_text(payload)
    messages = payload.get("messages") or []
    context_lines: list[str] = []
    for message in messages[-8:]:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if not role or not content or role == "system":
            continue
        context_lines.append(f"{role}: {content}")
    if context_lines:
        return (
            "Conversation context:\n"
            + "\n".join(context_lines)
            + "\n\nCurrent request:\n"
            + latest
            + "\n\nUse local and web tools when they help answer accurately."
        )
    if latest:
        return latest + "\n\nUse local and web tools when they help answer accurately."
    return "Use local and web tools when they help answer accurately."


def extract_system_prompt(payload: dict) -> str | None:
    parts: list[str] = []
    system_value = str(payload.get("system", "")).strip()
    if system_value:
        parts.append(system_value)
    for message in payload.get("messages") or []:
        if not isinstance(message, dict):
            continue
        if message.get("role") != "system":
            continue
        content = str(message.get("content", "")).strip()
        if content:
            parts.append(content)
    if not parts:
        return None
    return "\n\n".join(parts)


def build_ollama_chat_response(payload: dict, result) -> dict:
    model = str(payload.get("model", "showcase-wrapper"))
    return {
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": {"role": "assistant", "content": result.message},
        "done": True,
        "done_reason": "stop",
        "showcase": {
            "ok": result.ok,
            "tool_calls": [
                {
                    "tool_name": call.tool_name,
                    "ok": call.ok,
                    "summary": call.summary,
                    "data": call.data,
                }
                for call in result.tool_calls
            ],
        },
    }


def build_ollama_generate_response(payload: dict, result) -> dict:
    model = str(payload.get("model", "showcase-wrapper"))
    return {
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "response": result.message,
        "done": True,
        "done_reason": "stop",
        "context": [],
        "showcase": {
            "ok": result.ok,
            "tool_calls": [
                {
                    "tool_name": call.tool_name,
                    "ok": call.ok,
                    "summary": call.summary,
                    "data": call.data,
                }
                for call in result.tool_calls
            ],
        },
    }


def stream_chat_chunks(payload: dict, result) -> list[dict]:
    model = str(payload.get("model", "showcase-wrapper"))
    created_at = datetime.now(timezone.utc).isoformat()
    chunks = [
        {
            "model": model,
            "created_at": created_at,
            "message": {"role": "assistant", "content": chunk},
            "done": False,
        }
        for chunk in _chunk_text(result.message)
    ]
    chunks.append(
        {
            "model": model,
            "created_at": created_at,
            "message": {"role": "assistant", "content": ""},
            "done": True,
            "done_reason": "stop",
            "showcase": {
                "ok": result.ok,
                "tool_calls": [
                    {
                        "tool_name": call.tool_name,
                        "ok": call.ok,
                        "summary": call.summary,
                        "data": call.data,
                    }
                    for call in result.tool_calls
                ],
            },
        }
    )
    return chunks


def stream_generate_chunks(payload: dict, result) -> list[dict]:
    model = str(payload.get("model", "showcase-wrapper"))
    created_at = datetime.now(timezone.utc).isoformat()
    chunks = [
        {
            "model": model,
            "created_at": created_at,
            "response": chunk,
            "done": False,
        }
        for chunk in _chunk_text(result.message)
    ]
    chunks.append(
        {
            "model": model,
            "created_at": created_at,
            "response": "",
            "done": True,
            "done_reason": "stop",
            "context": [],
            "showcase": {
                "ok": result.ok,
                "tool_calls": [
                    {
                        "tool_name": call.tool_name,
                        "ok": call.ok,
                        "summary": call.summary,
                        "data": call.data,
                    }
                    for call in result.tool_calls
                ],
            },
        }
    )
    return chunks


def _chunk_text(text: str, *, max_chunk_size: int = 120) -> list[str]:
    stripped = text or ""
    if not stripped:
        return [""]
    words = stripped.split()
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
    return chunks or [stripped]


def _upstream_base(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    base_path = parsed.path
    if base_path.endswith("/api/chat"):
        base_path = base_path[: -len("/api/chat")]
    return f"{parsed.scheme}://{parsed.netloc}{base_path}"
