from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_static_ui_has_help_and_sidebar_history():
    index = (ROOT / "src" / "tooling_showcase" / "static" / "index.html").read_text(encoding="utf-8")
    assert 'data-page-target="help"' in index
    assert 'id="sidebarSessionHistory"' in index
    assert "Ollama and models" in index


def test_static_ui_does_not_ship_hardcoded_suggested_models():
    app = (ROOT / "src" / "tooling_showcase" / "static" / "app.js").read_text(encoding="utf-8")
    assert "Benchmarked profiles" in app
    assert "Suggested profiles" not in app
    assert "const MODEL_PROFILES" not in app


def test_static_ui_hotlinks_web_sources():
    app = (ROOT / "src" / "tooling_showcase" / "static" / "app.js").read_text(encoding="utf-8")
    assert "source-title-link" in app
    assert "source-url-link" in app
    assert 'target="_blank"' in app
    assert 'rel="noopener noreferrer"' in app
    assert "function safeHttpUrl" in app


def test_settings_button_toggles_modal_visibility():
    app = (ROOT / "src" / "tooling_showcase" / "static" / "app.js").read_text(encoding="utf-8")
    assert "function toggleSettings" in app
    assert 'addEventListener("click", toggleSettings)' in app
    assert "Close settings" in app


def test_static_ui_records_local_storage_schema_version():
    app = (ROOT / "src" / "tooling_showcase" / "static" / "app.js").read_text(encoding="utf-8")
    assert 'schema: "showcase.ui.schema.v1"' in app
    assert "const LOCAL_STORAGE_SCHEMA_VERSION = 3" in app
