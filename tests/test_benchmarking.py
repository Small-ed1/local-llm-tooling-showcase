from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import json

import tooling_showcase.benchmarking as benchmarking_module
from tooling_showcase.benchmarking import (
    BenchmarkTask,
    benchmark_command,
    derive_profiles,
    load_benchmark_results,
    run_benchmarks,
    save_benchmark_results,
    score_response,
)
from tooling_showcase.config import OllamaConfig, ShellPolicy, ShowcaseConfig
from tooling_showcase.models import ActionResult
from tooling_showcase.tool_protocol import visible_tool_schemas
from tooling_showcase.tools import ToolRuntime


def test_score_response_rewards_terms_and_json():
    task = BenchmarkTask(
        "extract",
        "structured",
        "Return JSON",
        ("read_file", "README.md"),
        expects_json=True,
    )
    score = score_response(task, '{"tool_name":"read_file","path":"README.md"}', ok=True, latency_seconds=0.1)
    assert score["score"] > 80
    assert set(score["term_hits"]) == {"read_file", "README.md"}


def test_derive_profiles_uses_best_category_score():
    results = {
        "suite_version": "test",
        "models": {
            "slow:latest": {"categories": {"coding": {"score": 70, "latency_seconds": 5}}},
            "fast:latest": {"categories": {"coding": {"score": 91, "latency_seconds": 3}}},
        },
    }
    profiles = derive_profiles(results)
    assert profiles["coding"]["model"] == "fast:latest"
    assert profiles["coding"]["benchmark_score"] == 91


def test_benchmark_results_round_trip(tmp_path: Path):
    path = tmp_path / "state" / "model_benchmarks.json"
    payload = {"suite_version": "test", "models": {"a": {}}, "profiles": {}, "last_inventory": ["a"]}
    save_benchmark_results(path, payload)
    assert load_benchmark_results(path)["models"] == {"a": {}}


def test_benchmark_inventory_command_lists_models(tmp_path: Path, monkeypatch, capsys):
    config = _benchmark_config(tmp_path)
    monkeypatch.setattr(benchmarking_module, "list_ollama_models", lambda config: (["demo:latest"], None))

    status = benchmark_command(
        config,
        Namespace(shell_summary=False, list_models=True, model=[], all=False, limit_tasks=None),
    )
    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    assert payload["model_count"] == 1
    assert payload["models"] == ["demo:latest"]


def test_benchmark_smoke_runs_limited_tasks_when_ollama_available(tmp_path: Path, monkeypatch):
    config = _benchmark_config(tmp_path)
    monkeypatch.setattr(benchmarking_module, "list_ollama_models", lambda config: (["demo:latest"], None))

    class FakeOllamaClient:
        def __init__(self, config):
            self.config = config

        def ask(self, prompt, **kwargs):
            return ActionResult(True, "Local-first tools need safeguards when things go wrong.")

    monkeypatch.setattr(benchmarking_module, "OllamaClient", FakeOllamaClient)

    result = run_benchmarks(config, max_tasks=1)
    stored = load_benchmark_results(config.benchmark_path)

    assert result["ok"] is True
    assert result["ran_models"] == ["demo:latest"]
    assert stored["models"]["demo:latest"]["tasks"][0]["id"] == "general_constraints"
    assert len(stored["models"]["demo:latest"]["tasks"]) == 1


def test_memory_tools_are_planner_visible(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runtime = ToolRuntime(
        ShowcaseConfig(
            project_root=tmp_path,
            workspace_root=workspace,
            portfolio_root=tmp_path,
            journal_path=tmp_path / "state" / "events.jsonl",
            ollama=OllamaConfig(enabled=False),
            shell_policy=ShellPolicy(),
        )
    )
    visible = {schema["name"] for schema in visible_tool_schemas(runtime.available_tools())}
    assert {"create_memory", "edit_memory", "delete_memory", "list_memories", "load_memory"} <= visible
    assert {"tool_structure", "local_doc_search", "local_doc_read"} <= visible
    assert "local_doc_replace" not in visible


def _benchmark_config(tmp_path: Path) -> ShowcaseConfig:
    return ShowcaseConfig(
        project_root=tmp_path,
        workspace_root=tmp_path,
        portfolio_root=tmp_path,
        journal_path=tmp_path / "state" / "events.jsonl",
        ollama=OllamaConfig(enabled=True),
        shell_policy=ShellPolicy(),
        benchmark_path=tmp_path / "state" / "model_benchmarks.json",
    )
