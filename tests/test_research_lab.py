from pathlib import Path

from tooling_showcase.config import load_config
from tooling_showcase.research import ResearchLab
from tooling_showcase.service import ShowcaseService


def test_research_lab_creates_and_runs_local_session(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n\nToolRuntime and research notes.\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "server.py").write_text("def run_server(): pass\n", encoding="utf-8")
    config = load_config(tmp_path)
    config.project_root = tmp_path
    config.workspace_root = tmp_path

    service = ShowcaseService(config)
    lab = ResearchLab(service)

    session = lab.start("research sidecar prototype", mode="local", depth=2)
    assert session["status"] == "planned"
    assert session["plan"]

    complete = lab.run(session["id"])
    assert complete["status"] == "complete"
    assert complete["report"].startswith("# Research Lab Report")
    assert complete["sources"]
    assert (tmp_path / "state" / "research" / "sessions" / f"{session['id']}.json").exists()
