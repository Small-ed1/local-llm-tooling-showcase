from pathlib import Path

from tooling_showcase.config import load_config
from tooling_showcase.config import OllamaConfig
from tooling_showcase.models import ActionResult
from tooling_showcase.research import ResearchLab
from tooling_showcase.research.modeler import ResearchModeler
from tooling_showcase.research.schemas import ResearchSession
from tooling_showcase.service import ShowcaseService


def test_research_lab_creates_and_runs_local_session(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n\nToolRuntime and research notes.\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "server.py").write_text("def run_server(): pass\n", encoding="utf-8")
    config = load_config(tmp_path)
    config.project_root = tmp_path
    config.workspace_root = tmp_path
    config.ollama.enabled = False

    service = ShowcaseService(config)
    lab = ResearchLab(service)

    session = lab.start("research workflow prototype", mode="local", depth=2)
    assert session["status"] == "planned"
    assert session["plan"]

    complete = lab.run(session["id"])
    assert complete["status"] == "complete"
    assert complete["report"].startswith("# Research Lab Report")
    assert complete["sources"]
    assert [call["stage"] for call in complete["model_calls"]] == ["research.plan", "research.source_plan", "research.extract", "research.report"]
    assert (tmp_path / "state" / "research" / "sessions" / f"{session['id']}.json").exists()


def test_research_lab_updates_planned_session(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    config = load_config(tmp_path)
    config.project_root = tmp_path
    config.workspace_root = tmp_path
    config.ollama.enabled = False
    lab = ResearchLab(ShowcaseService(config))

    session = lab.start("old goal", mode="local", depth=1)
    updated = lab.update(session["id"], goal="new hybrid goal", mode="hybrid", depth=3)

    assert updated["goal"] == "new hybrid goal"
    assert updated["mode"] == "hybrid"
    assert updated["depth"] == 3
    assert updated["status"] == "planned"
    assert updated["plan"] != session["plan"]
    assert updated["sources"] == []
    assert [call["stage"] for call in updated["model_calls"]] == ["research.plan", "research.plan"]


def test_research_modeler_uses_reasoning_model_with_thinking():
    seen = []

    class FakeOllama:
        config = OllamaConfig(enabled=True)

        def ask(self, prompt, **kwargs):
            seen.append(kwargs)
            return ActionResult(True, '{"steps":["inspect sources","extract claims"]}', data={"thinking": "reasoned"})

    modeler = ResearchModeler(FakeOllama())
    steps, trace = modeler.plan("map the backend", mode="local", depth=2, fallback=[])

    assert steps == ["inspect sources", "extract claims"]
    assert seen[0]["model"] == "qwen2.5:14b-instruct"
    assert seen[0]["think"] is True
    assert trace["thinking"] == "reasoned"


def test_research_modeler_creates_safe_llm_tool_plan():
    class FakeOllama:
        config = OllamaConfig(enabled=True)

        def ask(self, prompt, **kwargs):
            return ActionResult(
                True,
                '{"tools":[{"tool":"read_file","args":{"path_text":"README.md"},"title":"README"},{"tool":"shell_command","args":{"command":"pwd"},"title":"unsafe"}]}',
            )

    session = ResearchSession(id="research_test", goal="map backend", mode="local", depth=1, plan=["read docs"])
    calls, trace = ResearchModeler(FakeOllama()).source_plan(session, fallback=[])

    assert trace["stage"] == "research.source_plan"
    assert calls == [("read_file", {"path_text": "README.md"}, "README")]
