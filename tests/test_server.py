from tooling_showcase.server import _html_page, _manual_tool_api_disabled_payload, _manual_tool_api_enabled


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
