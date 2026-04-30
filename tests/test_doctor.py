import json
from pathlib import Path

from tooling_showcase.config import OllamaConfig, ShellPolicy, ShowcaseConfig
from tooling_showcase.doctor import collect_doctor_checks, run_doctor


ROOT = Path(__file__).resolve().parents[1]


def make_config(tmp_path: Path) -> ShowcaseConfig:
    return ShowcaseConfig(
        project_root=ROOT,
        workspace_root=ROOT,
        portfolio_root=ROOT.parent,
        journal_path=tmp_path / "state" / "events.jsonl",
        ollama=OllamaConfig(enabled=False),
        shell_policy=ShellPolicy(),
        benchmark_path=tmp_path / "state" / "model_benchmarks.json",
    )


def test_doctor_reports_core_checks_without_requiring_ollama(tmp_path: Path):
    checks = collect_doctor_checks(make_config(tmp_path))
    by_name = {check["name"]: check for check in checks}

    assert by_name["python"]["status"] == "ok"
    assert by_name["static_ui"]["status"] == "ok"
    assert by_name["frontend_js"]["status"] == "ok"
    assert by_name["ollama"]["status"] == "warn"


def test_doctor_json_output_is_machine_readable(tmp_path: Path, capsys):
    status = run_doctor(make_config(tmp_path), json_output=True)

    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["ok"] is True
    assert payload["version"] == "1.0.0"
