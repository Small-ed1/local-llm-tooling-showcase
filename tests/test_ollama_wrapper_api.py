from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace
from urllib.request import Request, urlopen
import json
import socket
import time

from tooling_showcase.models import ActionResult
from tooling_showcase.ollama_wrapper import build_service_request_text, run_ollama_wrapper


def test_wrapper_single_user_request_preserves_direct_tool_text():
    payload = {"messages": [{"role": "user", "content": "find file README"}]}

    assert build_service_request_text(payload) == "find file README"


def test_wrapper_chat_passes_showcase_control_flags():
    captured = {}

    class FakeService:
        config = SimpleNamespace(
            ollama=SimpleNamespace(timeout_seconds=1),
            shell_policy=SimpleNamespace(timeout_seconds=2),
        )

        def handle(self, text, **kwargs):
            captured["text"] = text
            captured["kwargs"] = kwargs
            return ActionResult(True, "handled")

    port = _free_port()
    thread = Thread(
        target=run_ollama_wrapper,
        args=(FakeService(),),
        kwargs={
            "host": "127.0.0.1",
            "port": port,
            "upstream_endpoint": "http://127.0.0.1:9/api/chat",
        },
        daemon=True,
    )
    thread.start()
    _wait_for_port(port)

    payload = json.dumps(
        {
            "model": "llama3.1:latest",
            "stream": False,
            "messages": [{"role": "user", "content": "hello"}],
            "showcase_allow_tools": False,
            "showcase_confirm": True,
            "showcase_max_tool_calls": 1,
        }
    ).encode("utf-8")
    req = Request(
        f"http://127.0.0.1:{port}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=5) as response:
        body = json.loads(response.read().decode("utf-8"))

    assert body["showcase"]["ok"] is True
    assert captured["kwargs"]["allow_tools"] is False
    assert captured["kwargs"]["confirm"] is True
    assert captured["kwargs"]["max_tool_calls"] == 1


def test_wrapper_proxies_upstream_ollama_paths():
    seen = []

    class FakeService:
        config = SimpleNamespace(
            ollama=SimpleNamespace(timeout_seconds=1),
            shell_policy=SimpleNamespace(timeout_seconds=2),
        )

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            seen.append(self.path)
            body = json.dumps({"path": self.path}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A003
            return

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()

    port = _free_port()
    thread = Thread(
        target=run_ollama_wrapper,
        args=(FakeService(),),
        kwargs={
            "host": "127.0.0.1",
            "port": port,
            "upstream_endpoint": f"http://127.0.0.1:{upstream.server_port}/api/chat",
        },
        daemon=True,
    )
    thread.start()
    _wait_for_port(port)

    with urlopen(f"http://127.0.0.1:{port}/api/tags", timeout=5) as response:
        body = json.loads(response.read().decode("utf-8"))
    upstream.shutdown()
    upstream_thread.join(timeout=5)

    assert body["path"] == "/api/tags"
    assert seen == ["/api/tags"]


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_for_port(port: int) -> None:
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError(f"wrapper did not start on port {port}")
