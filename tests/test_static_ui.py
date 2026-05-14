import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "src" / "tooling_showcase" / "static"
STATIC_JS_FILES = ["app-data.js", "markdown.js", "app.js"]


def static_js() -> str:
    return "\n".join((STATIC_DIR / name).read_text(encoding="utf-8") for name in STATIC_JS_FILES)


def test_static_ui_has_help_and_sidebar_history():
    index = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert 'data-page-target="help"' in index
    assert 'id="sidebarSessionHistory"' in index
    assert "Ollama and models" in index
    assert index.index("/static/app-data.js") < index.index("/static/markdown.js") < index.index("/static/app.js")


def test_tool_docs_use_shared_json_source():
    from tooling_showcase.server_metadata import TOOL_DOCS

    docs = json.loads((STATIC_DIR / "tool_docs.json").read_text(encoding="utf-8"))
    app_data = (STATIC_DIR / "app-data.js").read_text(encoding="utf-8")
    app = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert docs["read_file"]["summary"] == TOOL_DOCS["read_file"]["summary"]
    assert docs["shell_command"]["example"] == TOOL_DOCS["shell_command"]["example"]
    assert "const TOOL_DOCS = {}" in app_data
    assert "const TOOL_EXAMPLES = {}" in app_data
    assert "/static/tool_docs.json" in app


def test_app_data_script_exports_required_constants():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")

    script = f"""
const fs = require("fs");
const vm = require("vm");
const code = fs.readFileSync({str(STATIC_DIR / "app-data.js")!r}, "utf8");
const sandbox = {{}};
sandbox.globalThis = sandbox;
vm.runInNewContext(code, sandbox, {{ filename: "app-data.js" }});
const data = sandbox.ShowcaseData;
if (!data) throw new Error("ShowcaseData missing");
if (data.CHAT_CONTEXT_MAX_MESSAGES !== 24) throw new Error("bad max messages");
if (data.CHAT_CONTEXT_MAX_CHARS !== 24000) throw new Error("bad max chars");
if (!data.PLANNER_SAFE_TOOLS.has("local_doc_search")) throw new Error("local docs missing");
"""
    subprocess.run([node, "-e", script], check=True)


def test_static_ui_does_not_ship_hardcoded_suggested_models():
    js = static_js()
    assert "Benchmarked profiles" in js
    assert "Suggested profiles" not in js
    assert "const MODEL_PROFILES" not in js


def test_static_ui_hotlinks_web_sources():
    js = static_js()
    assert "source-title-link" in js
    assert "source-url-link" in js
    assert 'target="_blank"' in js
    assert 'rel="noopener noreferrer"' in js
    assert "function safeHttpUrl" in js


def test_settings_button_toggles_modal_visibility():
    app = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "function toggleSettings" in app
    assert 'addEventListener("click", toggleSettings)' in app
    assert "Close settings" in app
    assert "HTTP ${res.status}" in app


def test_static_ui_records_local_storage_schema_version():
    js = static_js()
    assert 'schema: "showcase.ui.schema.v1"' in js
    assert "const LOCAL_STORAGE_SCHEMA_VERSION = 3" in js


def test_static_ui_exposes_runtime_timeout_settings():
    index = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    js = static_js()

    assert 'id="settingsOllamaTimeout"' in index
    assert 'id="settingsToolTimeout"' in index
    assert "ollama_timeout_seconds" in js
    assert "tool_timeout_seconds" in js


def test_static_ui_has_user_mode_archive_imports_and_expanded_ollama_options():
    index = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    js = static_js()

    assert 'id="settingsModeSelect"' in index
    assert 'id="archiveList"' in index
    assert 'id="systemPromptImportInput"' in index
    assert 'id="profileImportInput"' in index
    assert 'id="memoriesImportInput"' in index
    assert "num_keep" in js
    assert "presence_penalty" in js
    assert "frequency_penalty" in js
    assert "use_mmap" in js
    assert "THEME_PRESETS" in js
    assert "SYSTEM_PROMPT_PRESETS" in js


def test_markdown_renderer_escapes_html_and_links_web_sources():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")

    script = f"""
const fs = require("fs");
const vm = require("vm");
const code = fs.readFileSync({str(STATIC_DIR / "markdown.js")!r}, "utf8");
const sandbox = {{}};
sandbox.globalThis = sandbox;
vm.runInNewContext(code, sandbox, {{ filename: "markdown.js" }});
const html = sandbox.ShowcaseMarkdown.renderSafeMarkdown("# Title\\n\\nSee [docs](https://example.com) and `<tag>`.\\n\\n```js\\nconst x = 1 < 2;\\n```");
if (!html.includes("<h3>Title</h3>")) throw new Error(html);
if (!html.includes('href="https://example.com" target="_blank" rel="noopener noreferrer"')) throw new Error(html);
if (!html.includes("<code>&lt;tag&gt;</code>")) throw new Error(html);
if (!html.includes('data-language="js"')) throw new Error(html);
if (!html.includes("1 &lt; 2")) throw new Error(html);
"""
    subprocess.run([node, "-e", script], check=True)
