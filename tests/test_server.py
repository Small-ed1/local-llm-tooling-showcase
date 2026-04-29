from tooling_showcase.server import _html_page


def test_web_ui_contains_chat_and_run_controls():
    page = _html_page()
    assert "Local Assistant App" in page
    assert 'id="tab-ask"' in page
    assert 'id="tab-run"' in page
    assert 'id="ask-chip"' in page
    assert 'id="run-chip"' in page
    assert 'id="preset"' in page
    assert 'value="small_ed"' in page
    assert 'value="mallow"' in page
    assert 'id="prompt"' in page
    assert 'id="system-prompt"' in page
    assert 'id="stream-mode"' in page
    assert 'id="max-steps"' in page
    assert 'id="preset-list-buttons"' in page
    assert 'id="inspector-tools"' in page
    assert 'id="panel-assets"' in page
    assert "/api/tools" in page
    assert "/api/run" in page
