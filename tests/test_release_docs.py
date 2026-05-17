from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_package_version_is_v1_1():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    init_text = (ROOT / "src" / "tooling_showcase" / "__init__.py").read_text(encoding="utf-8")

    assert metadata["project"]["version"] == "1.1.0"
    assert '__version__ = "1.1.0"' in init_text


def test_readme_release_status_and_known_limits_are_prominent():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Current release: `v1.1.0`" in readme
    assert readme.index("## Known Limits") < readme.index("## Screenshots")


def test_desktop_integration_docs_and_assets_exist():
    assert (ROOT / "docs" / "desktop-integration.md").is_file()
    assert (ROOT / "src" / "tooling_showcase" / "desktop" / "assets" / "linux" / "README.md").is_file()
    assert (ROOT / "src" / "tooling_showcase" / "desktop" / "assets" / "windows" / "README.md").is_file()
    assert (ROOT / "src" / "tooling_showcase" / "desktop" / "assets" / "macos" / "README.md").is_file()


def test_readme_screenshot_paths_exist():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    markdown_paths = re.findall(r"!\[[^\]]*\]\((docs/screenshots/[^)]+)\)", readme)
    html_paths = re.findall(r'<img src="(docs/screenshots/[^"]+)"', readme)

    paths = markdown_paths + html_paths
    assert paths
    for path in paths:
        assert (ROOT / path).is_file(), path
