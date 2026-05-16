import sys

from tooling_showcase.cli import build_parser, main


def test_serve_commands_default_to_loopback():
    parser = build_parser()

    serve = parser.parse_args(["serve"])
    wrapper = parser.parse_args(["serve-ollama"])

    assert serve.host == "127.0.0.1"
    assert wrapper.host == "127.0.0.1"


def test_lan_binding_requires_explicit_host():
    parser = build_parser()

    serve = parser.parse_args(["serve", "--host", "0.0.0.0"])

    assert serve.host == "0.0.0.0"
    assert serve.enable_remote_tool_api is False


def test_serve_supports_remote_tool_api_opt_in():
    parser = build_parser()

    serve = parser.parse_args(["serve", "--host", "0.0.0.0", "--enable-remote-tool-api"])

    assert serve.host == "0.0.0.0"
    assert serve.enable_remote_tool_api is True


def test_doctor_command_supports_json_output():
    parser = build_parser()

    doctor = parser.parse_args(["doctor", "--json"])

    assert doctor.command == "doctor"
    assert doctor.json is True


def test_runtime_commands_support_timeout_options():
    parser = build_parser()

    ask = parser.parse_args(["ask", "hello", "--ollama-timeout", "240", "--tool-timeout", "45"])
    serve = parser.parse_args(["serve", "--ollama-timeout", "180", "--tool-timeout", "60"])
    wrapper = parser.parse_args(["serve-ollama", "--ollama-timeout", "300", "--tool-timeout", "90"])

    assert ask.ollama_timeout == 240
    assert ask.tool_timeout == 45
    assert serve.ollama_timeout == 180
    assert serve.tool_timeout == 60
    assert wrapper.ollama_timeout == 300
    assert wrapper.tool_timeout == 90


def test_cli_ask_find_file_readme_without_ollama(tmp_path, monkeypatch, capsys):
    (tmp_path / "README.md").write_text("demo readme", encoding="utf-8")
    _isolate_cli_state(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", ["tooling-showcase", "ask", "find file README"])

    status = main()
    output = capsys.readouterr().out

    assert status == 0
    assert "README.md" in output
    assert "Tool calls:" in output


def test_cli_research_local_runs_under_state_research(tmp_path, monkeypatch, capsys):
    (tmp_path / "README.md").write_text("# Demo\n\nResearch demo notes.\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    _isolate_cli_state(tmp_path, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tooling-showcase",
            "research",
            "local demo research",
            "--mode",
            "local",
            "--depth",
            "1",
        ],
    )

    status = main()
    output = capsys.readouterr().out
    research_root = tmp_path / "state" / "research"

    assert status == 0
    assert "# Research Lab Report" in output
    assert list((research_root / "sessions").glob("*.json"))
    assert list((research_root / "reports").glob("*.md"))
    assert not list((tmp_path / "state").glob("research_*.json"))
    assert not list((tmp_path / "state").glob("research_*.md"))


def _isolate_cli_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOOLING_SHOWCASE_OLLAMA_ENABLED", "false")
    monkeypatch.setenv("TOOLING_SHOWCASE_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("TOOLING_SHOWCASE_PORTFOLIO", str(tmp_path))
    monkeypatch.setenv("TOOLING_SHOWCASE_JOURNAL", str(tmp_path / "state" / "events.jsonl"))
    monkeypatch.setenv("TOOLING_SHOWCASE_BENCHMARKS", str(tmp_path / "state" / "model_benchmarks.json"))
