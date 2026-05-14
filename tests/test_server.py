from http import HTTPStatus

from tooling_showcase.server import (
    JsonBodyError,
    _html_page,
    _manual_tool_api_disabled_payload,
    _manual_tool_api_enabled,
    _stabilize_ollama_options,
)


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
