from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.request import Request, urlopen
import json
import socket
import time

from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.ollama_wrapper import (
    _upstream_base,
    build_ollama_generate_response,
    build_ollama_chat_response,
    build_service_request_text,
    extract_system_prompt,
    extract_chat_text,
    extract_latest_user_text,
    run_ollama_wrapper,
    stream_chat_chunks,
    stream_generate_chunks,
)


def test_extract_chat_text_prefers_user_messages():
    payload = {
        "messages": [
            {"role": "system", "content": "ignore"},
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "ignore"},
            {"role": "user", "content": "second"},
        ]
    }
    assert extract_chat_text(payload) == "first\n\nsecond"


def test_extract_chat_text_falls_back_to_prompt():
    assert extract_chat_text({"prompt": "single prompt"}) == "single prompt"


def test_extract_latest_user_text_prefers_latest_user_message():
    payload = {
        "messages": [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "latest"},
        ]
    }
    assert extract_latest_user_text(payload) == "latest"


def test_build_service_request_text_includes_recent_context():
    payload = {
        "messages": [
            {"role": "system", "content": "You are a pirate."},
            {"role": "user", "content": "what repo is this"},
            {"role": "assistant", "content": "It is a tooling project."},
            {"role": "user", "content": "search the web for ollama wrappers"},
        ]
    }
    text = build_service_request_text(payload)
    assert "Conversation context:" in text
    assert "assistant: It is a tooling project." in text
    assert "system: You are a pirate." not in text
    assert "Current request:" in text
    assert "search the web for ollama wrappers" in text
    assert "what repo is this\n\nsearch the web for ollama wrappers" not in text
    assert "Use local and web tools" in text


def test_extract_system_prompt_prefers_payload_and_system_messages():
    payload = {
        "system": "Stay in character.",
        "messages": [
            {"role": "system", "content": "You are Captain Redbeard."},
            {"role": "user", "content": "Who are you?"},
        ],
    }
    system_prompt = extract_system_prompt(payload)
    assert system_prompt is not None
    assert "Stay in character." in system_prompt
    assert "You are Captain Redbeard." in system_prompt


def test_build_ollama_chat_response_includes_showcase_metadata():
    result = ActionResult(
        True,
        "done",
        tool_calls=[ToolCall("read_file", True, "README contents")],
    )
    payload = {"model": "llama3.1:latest"}
    response = build_ollama_chat_response(payload, result)
    assert response["model"] == "llama3.1:latest"
    assert response["message"]["content"] == "done"
    assert response["showcase"]["tool_calls"][0]["tool_name"] == "read_file"


def test_build_ollama_generate_response_includes_showcase_metadata():
    result = ActionResult(
        True,
        "done",
        tool_calls=[ToolCall("web_search", True, "result")],
    )
    payload = {"model": "llama3.1:latest"}
    response = build_ollama_generate_response(payload, result)
    assert response["model"] == "llama3.1:latest"
    assert response["response"] == "done"
    assert response["showcase"]["tool_calls"][0]["tool_name"] == "web_search"


def test_stream_chunk_helpers_emit_done_payload():
    result = ActionResult(
        True, "one two three", tool_calls=[ToolCall("read_file", True, "ok")]
    )
    chat = stream_chat_chunks({"model": "llama3.1:latest"}, result)
    generate = stream_generate_chunks({"model": "llama3.1:latest"}, result)
    assert chat[-1]["done"] is True
    assert chat[-1]["showcase"]["tool_calls"][0]["tool_name"] == "read_file"
    assert generate[-1]["done"] is True
    assert generate[-1]["showcase"]["tool_calls"][0]["tool_name"] == "read_file"


def test_wrapper_end_to_end_streaming_chat():
    class FakeService:
        def handle(self, text, confirm=False, model=None, system_prompt=None):
            return ActionResult(
                True,
                "hello from wrapper",
                tool_calls=[ToolCall("web_search", True, "summary")],
            )

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            body = json.dumps({"models": []}).encode("utf-8")
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

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

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
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)

    payload = json.dumps(
        {
            "model": "llama3.1:latest",
            "stream": True,
            "messages": [{"role": "user", "content": "hello"}],
        }
    ).encode("utf-8")
    req = Request(
        f"http://127.0.0.1:{port}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=5) as response:
        body = response.read().decode("utf-8")
    upstream.shutdown()
    upstream_thread.join(timeout=5)

    lines = [json.loads(line) for line in body.splitlines() if line.strip()]
    assert lines[-1]["done"] is True
    assert lines[-1]["showcase"]["tool_calls"][0]["tool_name"] == "web_search"


def test_upstream_base_strips_chat_suffix():
    assert _upstream_base("http://127.0.0.1:11434/api/chat") == "http://127.0.0.1:11434"
