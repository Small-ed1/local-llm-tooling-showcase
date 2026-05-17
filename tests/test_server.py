from http import HTTPStatus
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import socket
import time

from tooling_showcase.config import OllamaConfig, ShellPolicy, ShowcaseConfig
from tooling_showcase.models import ActionResult
from tooling_showcase.server import (
    JsonBodyError,
    _html_page,
    _manual_tool_api_disabled_payload,
    _manual_tool_api_enabled,
    _stabilize_ollama_options,
    run_server,
)
from tooling_showcase.service import ShowcaseService


def test_web_ui_contains_chat_and_run_controls():
    page = _html_page()
    assert "Local LLM Tooling Showcase" in page
    assert 'id="promptInput"' in page
    assert 'id="sendBtn"' in page
    assert 'id="toolSelect"' in page
    assert 'id="runToolBtn"' in page
    assert 'id="composerRunTaskBtn"' in page
    assert 'id="settingsModal"' in page
    assert 'data-page-target="tools"' in page
    assert 'data-page-target="journal"' in page
    assert 'src="/static/app-data.js"' in page
    assert 'src="/static/markdown.js"' in page
    assert 'src="/static/app.js"' in page
    assert "legacy test markers" not in page


def test_manual_tool_api_requires_loopback_or_explicit_remote_opt_in(monkeypatch):
    monkeypatch.delenv("TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API", raising=False)
    assert _manual_tool_api_enabled("127.0.0.1") is True
    assert _manual_tool_api_enabled("localhost") is True
    assert _manual_tool_api_enabled("::1") is True
    assert _manual_tool_api_enabled("0.0.0.0") is False
    assert _manual_tool_api_enabled("0.0.0.0", enable_remote_tool_api=True) is True

    monkeypatch.setenv("TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API", "1")
    assert _manual_tool_api_enabled("0.0.0.0") is True
    assert _manual_tool_api_disabled_payload("0.0.0.0")["ok"] is False


def test_server_preserves_user_ollama_option_overrides():
    opts = _stabilize_ollama_options(
        {
            "num_ctx": 8192,
            "num_batch": 64,
            "num_gpu": 3,
            "main_gpu": 1,
            "num_thread": 12,
            "num_predict": 2048,
        }
    )

    assert opts["num_ctx"] == 8192
    assert opts["num_batch"] == 64
    assert opts["num_gpu"] == 3
    assert opts["main_gpu"] == 1
    assert opts["num_thread"] == 12
    assert opts["num_predict"] == 2048


def test_json_body_error_carries_http_status():
    error = JsonBodyError("too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
    assert error.message == "too large"
    assert error.status == HTTPStatus.REQUEST_ENTITY_TOO_LARGE


def test_api_chat_alias_supports_chat_options_tool_calls_and_streaming(tmp_path: Path):
    service = _make_service(tmp_path, ollama_enabled=True)
    seen = {}

    def fake_ask(prompt, **kwargs):
        seen["prompt"] = prompt
        seen["kwargs"] = kwargs
        return ActionResult(True, "Hello from chat. <END_OF_MESSAGE>")

    service.ollama.ask = fake_ask
    base_url = _start_server(service)

    status, data = _post_json(
        f"{base_url}/api/chat",
        {
            "text": "Say hello",
            "allow_tools": False,
            "model": "demo-model:latest",
            "options": {"temperature": 0.4},
            "ollama_timeout_seconds": 3,
            "tool_timeout_seconds": 4,
            "messages": [{"role": "user", "content": "Earlier context"}],
        },
    )

    assert status == HTTPStatus.OK
    assert data["ok"] is True
    assert data["message"] == "Hello from chat."
    assert seen["prompt"] == "Say hello"
    assert seen["kwargs"]["model"] == "demo-model:latest"
    assert seen["kwargs"]["timeout_seconds"] == 3
    assert seen["kwargs"]["options"]["temperature"] == 0.4
    assert seen["kwargs"]["messages"][-1] == {"role": "user", "content": "Say hello"}

    status, tool_data = _post_json(f"{base_url}/api/chat", {"text": "find file README"})
    assert status == HTTPStatus.OK
    assert tool_data["ok"] is True
    assert tool_data["tool_calls"][0]["tool_name"] == "file_search"
    assert "README.md" in tool_data["message"]

    status, content_type, body = _post_bytes(
        f"{base_url}/api/chat",
        {"text": "find file README", "stream": True},
    )
    chunks = [json.loads(line) for line in body.decode("utf-8").splitlines() if line.strip()]
    assert status == HTTPStatus.OK
    assert "application/x-ndjson" in content_type
    assert chunks[0]["type"] == "tool_start"
    assert chunks[-1]["type"] == "final"
    assert chunks[-1]["done"] is True
    assert chunks[-1]["tool_calls"][0]["tool_name"] == "file_search"


def test_manual_tool_api_loopback_works_and_remote_bind_blocks(tmp_path: Path):
    loopback_service = _make_service(tmp_path / "loopback", ollama_enabled=False)
    loopback_url = _start_server(loopback_service, host="127.0.0.1")

    status, data = _post_json(
        f"{loopback_url}/api/tool",
        {"tool": "file_search", "arguments": {"query": "README"}},
    )
    assert status == HTTPStatus.OK
    assert data["ok"] is True
    assert data["tool_call"]["tool_name"] == "file_search"

    remote_service = _make_service(tmp_path / "remote", ollama_enabled=False)
    remote_url = _start_server(remote_service, host="0.0.0.0")

    status, data = _post_json(
        f"{remote_url}/api/tool",
        {"tool": "file_search", "arguments": {"query": "README"}},
        expected_status=HTTPStatus.FORBIDDEN,
    )
    assert status == HTTPStatus.FORBIDDEN
    assert data["ok"] is False
    assert "disabled" in data["error"]


def test_desktop_status_endpoint_returns_json(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    service = _make_service(tmp_path / "desktop-endpoint", ollama_enabled=False)
    base_url = _start_server(service)

    with urlopen(f"{base_url}/api/desktop/status", timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))

    assert response.status == HTTPStatus.OK
    assert data["ok"] is True
    assert data["desktop"]["supported"] is True
    assert "launcher_installed" in data["desktop"]


def _make_service(root: Path, *, ollama_enabled: bool) -> ShowcaseService:
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "README.md").write_text("showcase readme", encoding="utf-8")
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    return ShowcaseService(
        ShowcaseConfig(
            project_root=root,
            workspace_root=workspace,
            portfolio_root=root,
            journal_path=state / "events.jsonl",
            ollama=OllamaConfig(enabled=ollama_enabled),
            shell_policy=ShellPolicy(),
            benchmark_path=state / "model_benchmarks.json",
        )
    )


def _start_server(
    service: ShowcaseService,
    *,
    host: str = "127.0.0.1",
    enable_remote_tool_api: bool = False,
) -> str:
    port = _free_port()
    thread = Thread(
        target=run_server,
        args=(service, host, port),
        kwargs={"enable_remote_tool_api": enable_remote_tool_api},
        daemon=True,
    )
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    _wait_for_http(base_url)
    return base_url


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_http(base_url: str, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(base_url, timeout=0.2) as response:
                if response.status == HTTPStatus.OK:
                    return
        except OSError:
            time.sleep(0.05)
    raise AssertionError(f"server did not start: {base_url}")


def _post_json(
    url: str,
    payload: dict,
    *,
    expected_status: HTTPStatus = HTTPStatus.OK,
) -> tuple[int, dict]:
    status, _, body = _post_bytes(url, payload, expected_status=expected_status)
    return status, json.loads(body.decode("utf-8"))


def _post_bytes(
    url: str,
    payload: dict,
    *,
    expected_status: HTTPStatus = HTTPStatus.OK,
) -> tuple[int, str, bytes]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except HTTPError as exc:
        if exc.code != int(expected_status):
            raise
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()
