from pathlib import Path

from tooling_showcase.config import OllamaConfig, ShellPolicy, ShowcaseConfig
from tooling_showcase.benchmarking import save_benchmark_results
from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.service import ShowcaseService
import tooling_showcase.service as service_module


def make_config(tmp_path: Path) -> ShowcaseConfig:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("showcase readme", encoding="utf-8")
    state = tmp_path / "state"
    state.mkdir(parents=True, exist_ok=True)
    return ShowcaseConfig(
        project_root=tmp_path,
        workspace_root=workspace,
        portfolio_root=tmp_path,
        journal_path=state / "events.jsonl",
        ollama=OllamaConfig(enabled=False),
        shell_policy=ShellPolicy(),
        benchmark_path=state / "model_benchmarks.json",
    )


def make_runtime(tmp_path: Path):
    from tooling_showcase.tools import ToolRuntime

    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    config = ShowcaseConfig(
        project_root=tmp_path,
        workspace_root=workspace,
        portfolio_root=tmp_path,
        journal_path=tmp_path / "state" / "events.jsonl",
        ollama=OllamaConfig(enabled=False, model="qwen3:8b"),
        shell_policy=ShellPolicy(timeout_seconds=10),
        benchmark_path=tmp_path / "state" / "model_benchmarks.json",
    )
    return ToolRuntime(config)


def test_service_runs_direct_file_search(tmp_path: Path):
    service = ShowcaseService(make_config(tmp_path))
    result = service.handle("find file README")
    assert result.ok is True
    assert "README.md" in result.message


def test_service_routes_project_inspection_to_tree_view(tmp_path: Path):
    service = ShowcaseService(make_config(tmp_path))
    state_dir = tmp_path / "state"
    state_dir.mkdir(exist_ok=True)
    (state_dir / "tasks.json").write_text("{}", encoding="utf-8")
    result = service.handle("look around this project and show me the structure")
    assert result.ok is True
    assert result.tool_calls[0].tool_name == "tree_view"
    assert "README.md" in result.message
    assert "state/" not in result.tool_calls[0].summary
    assert ".git/" not in result.tool_calls[0].summary


def test_service_logs_llm_fallback_without_ollama(tmp_path: Path):
    service = ShowcaseService(make_config(tmp_path))
    result = service.handle("how does this showcase work")
    assert result.ok is False
    assert "disabled" in result.message.lower()
    events = service.recent_events(limit=1)
    assert len(events) == 1
    assert events[0]["route"] == "llm_fallback"


def test_shell_command_policy_requires_confirm(tmp_path: Path):
    service = ShowcaseService(make_config(tmp_path))
    result = service.handle("run rm tmp.txt")
    assert result.ok is False
    assert "Confirmation required" in result.message


def test_adapter_inventory_tool(tmp_path: Path):
    service = ShowcaseService(make_config(tmp_path))
    result = service.handle("show adapters")
    assert result.ok is True
    assert "Northstar" in result.message


def test_model_cards_include_live_unbenchmarked_models(tmp_path: Path, monkeypatch):
    service = ShowcaseService(make_config(tmp_path))
    monkeypatch.setattr(service_module, "list_ollama_models", lambda config: (["qwen3:8b"], None))

    cards = service.model_cards()

    assert cards == [
        {
            "model": "qwen3:8b",
            "category": "unprofiled",
            "job": "run tooling-showcase benchmark to assign this model",
            "summary": "No local benchmark profile has been recorded yet.",
            "chat_capable": True,
        }
    ]


def test_service_allows_model_to_choose_and_run_tool(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    responses = iter(
        [
            ActionResult(
                True,
                '{"type":"tool_call","tool_name":"read_file","arguments":{"path":"README.md"}}',
            ),
            ActionResult(
                True,
                '{"type":"answer","message":"I read README.md successfully. <END_OF_MESSAGE>"}',
            ),
        ]
    )
    service.ollama.ask = lambda prompt, system_prompt=None, response_format=None: next(
        responses
    )
    result = service.handle("What does the README say?")
    assert result.ok is True
    assert result.message == "I read README.md successfully."
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "read_file"
    assert result.tool_calls[0].ok is True


def test_service_uses_deterministic_route_before_model_planner(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("planner should not be called for clean tree route")

    service.ollama.ask = fail_if_called
    result = service.handle("look around this project and show me the structure")
    assert result.ok is True
    assert result.tool_calls[0].tool_name == "tree_view"
    assert result.data["router"]["action"] == "tree_view"
    assert "README.md" in result.message


def test_service_returns_model_answer_when_no_tool_is_needed(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    service.ollama.ask = lambda prompt, system_prompt=None, response_format=None: (
        ActionResult(
            True,
            '{"type":"answer","message":"No tool needed. <END_OF_MESSAGE>"}',
        )
    )
    result = service.handle("Say hello")
    assert result.ok is True
    assert result.message == "No tool needed."
    assert result.tool_calls == []


def test_service_streams_direct_model_deltas(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)

    def stream_events(*args, **kwargs):
        yield {"type": "thinking_delta", "delta": "thinking"}
        yield {"type": "content_delta", "delta": "Hello"}
        yield {"type": "content_delta", "delta": " there"}
        yield {"type": "ollama_done", "data": {}}

    service.ollama.stream_events = stream_events
    events = list(service.stream_handle("Say hello"))

    assert [event["type"] for event in events] == ["thinking_delta", "content_delta", "content_delta", "final"]
    assert events[-1]["message"] == "Hello there"
    assert events[-1]["thinking"] == "thinking"


def test_service_streams_tool_start_and_result(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    responses = iter(
        [
            ActionResult(True, '{"type":"tool_call","tool_name":"read_file","arguments":{"path":"README.md"}}'),
            ActionResult(True, '{"type":"answer","message":"Read it. <END_OF_MESSAGE>"}'),
        ]
    )
    service.ollama.ask = lambda *args, **kwargs: next(responses)

    events = list(service.stream_handle("What does the README say?"))

    assert [event["type"] for event in events if event["type"].startswith("tool_")] == ["tool_start", "tool_result"]
    assert events[0]["tool_name"] == "read_file"
    assert events[1]["tool_call"]["ok"] is True
    assert events[-1]["type"] == "final"
    assert events[-1]["tool_calls"][0]["tool_name"] == "read_file"


def test_service_uses_benchmark_profile_for_auto_route(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    save_benchmark_results(
        config.benchmark_path,
        {
            "suite_version": "test",
            "models": {"bench-general:latest": {}},
            "profiles": {
                "general": {
                    "model": "bench-general:latest",
                    "category": "general",
                    "job": "default everyday assistant",
                    "summary": "benchmark selected",
                    "chat_capable": True,
                    "benchmark_score": 88,
                }
            },
            "last_inventory": ["bench-general:latest"],
        },
    )
    service = ShowcaseService(config)
    seen = {}

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, **kwargs):
        seen["model"] = model
        return ActionResult(True, "Benchmark route used.")

    service.ollama.ask = mock_ask
    result = service.handle("Say hello")
    assert result.ok is True
    assert seen["model"] == "bench-general:latest"
    assert result.data["model_route"]["benchmark_profile"] is True


def test_service_passes_model_override_to_ollama(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[str | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None):
        seen.append(model)
        return ActionResult(
            True,
            '{"type":"answer","message":"Used selected model. <END_OF_MESSAGE>"}',
        )

    service.ollama.ask = mock_ask
    result = service.handle("Say hello", model="qwen3:8b")
    assert result.ok is True
    assert result.message == "Used selected model."
    assert seen == ["qwen3:8b"]


def test_service_treats_auto_model_sentinels_as_no_override(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[str | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, **kwargs):
        seen.append(model)
        return ActionResult(
            True,
            '{"type":"answer","message":"Routed. <END_OF_MESSAGE>"}',
        )

    service.ollama.ask = mock_ask
    result = service.handle("this should be fast", model="None")
    assert result.ok is True
    assert result.message == "Routed."
    assert seen == ["llama3.2:latest"]


def test_service_disables_thinking_for_non_thinking_routed_models(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[bool | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, think=None, **kwargs):
        seen.append(think)
        return ActionResult(True, "Fast answer. <END_OF_MESSAGE>")

    service.ollama.ask = mock_ask
    result = service.handle("briefly say hello", options={"enable_thinking": True})
    assert result.ok is True
    assert result.message == "Fast answer."
    assert seen == [False]


def test_service_passes_ollama_options_override(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[dict | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, options=None):
        seen.append(options)
        return ActionResult(
            True,
            '{"type":"answer","message":"Tuned. <END_OF_MESSAGE>"}',
        )

    service.ollama.ask = mock_ask
    result = service.handle(
        "Say hello",
        ollama_options={"temperature": 0.55, "repeat_penalty": 1.2},
    )
    assert result.ok is True
    assert result.message == "Tuned."
    assert seen == [{"temperature": 0.55, "repeat_penalty": 1.2}]


def test_service_passes_response_format_to_final_model_call(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[str | dict | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, **kwargs):
        seen.append(response_format)
        return ActionResult(
            True,
            '{"answer":"structured"}',
        )

    service.ollama.ask = mock_ask
    result = service.handle("Return JSON", allow_tools=False, response_format="json")
    assert result.ok is True
    assert result.message == '{"answer":"structured"}'
    assert seen == ["json"]


def test_service_uses_direct_model_call_for_structured_chat_answer(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[str | dict | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, **kwargs):
        seen.append(response_format)
        return ActionResult(True, '{"answer":"structured"}')

    service.ollama.ask = mock_ask
    result = service.handle("Return JSON", response_format="json")
    assert result.ok is True
    assert result.message == '{"answer":"structured"}'
    assert seen == ["json"]


def test_service_auto_routes_coding_requests_to_coding_model(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[str | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None):
        seen.append(model)
        return ActionResult(
            True,
            '{"type":"answer","message":"Implemented. <END_OF_MESSAGE>"}',
        )

    service.ollama.ask = mock_ask
    result = service.handle("Debug this Python stack trace and fix the function")
    assert result.ok is True
    assert seen == ["qwen3.5:9b"]
    assert result.data["model_route"]["category"] == "coding"
    assert result.data["model_route"]["model"] == "qwen3.5:9b"


def test_service_auto_routes_summary_requests_to_summary_model(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[str | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None):
        seen.append(model)
        return ActionResult(
            True,
            '{"type":"answer","message":"Short recap. <END_OF_MESSAGE>"}',
        )

    service.ollama.ask = mock_ask
    result = service.handle("Summarize this architecture briefly")
    assert result.ok is True
    assert seen == ["dolphin3:latest"]
    assert result.data["model_route"]["category"] == "summary"


def test_service_passes_system_prompt_override_to_ollama(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    seen: list[str | None] = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None):
        seen.append(system_prompt)
        return ActionResult(
            True,
            '{"type":"answer","message":"Persona preserved. <END_OF_MESSAGE>"}',
        )

    service.ollama.ask = mock_ask
    result = service.handle("Who are you?", system_prompt="You are Captain Redbeard.")
    assert result.ok is True
    assert result.message == "Persona preserved."
    assert seen
    assert "You are Captain Redbeard." in seen[0]


def test_service_does_not_repeat_identical_tool_call(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    responses = iter(
        [
            ActionResult(
                True,
                '{"type":"tool_call","tool_name":"read_file","arguments":{"path":"README.md"}}',
            ),
            ActionResult(
                True,
                '{"type":"tool_call","tool_name":"read_file","arguments":{"path":"README.md"}}',
            ),
            ActionResult(
                True,
                '{"type":"answer","message":"Done. <END_OF_MESSAGE>"}',
            ),
        ]
    )

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None):
        return next(responses)

    service.ollama.ask = mock_ask
    result = service.handle("Read the README with a tool")
    assert result.ok is True
    read_calls = [call for call in result.tool_calls if call.tool_name == "read_file"]
    assert len(read_calls) == 1


def test_service_allows_model_memory_tools(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    responses = iter(
        [
            ActionResult(
                True,
                '{"action":"tool_call","tool_name":"create_memory","arguments":{"key":"style","value":"prefers direct answers"}}',
            ),
            ActionResult(
                True,
                '{"action":"answer","answer":"I will remember that. <END_OF_MESSAGE>"}',
            ),
        ]
    )

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, **kwargs):
        return next(responses)

    service.ollama.ask = mock_ask
    result = service.handle("Remember that I prefer direct answers")
    assert result.ok is True
    assert result.tool_calls[0].tool_name == "create_memory"
    assert result.tool_calls[0].ok is True
    loaded = service.tools.load_memory("style")
    assert loaded.ok is True
    assert "direct" in loaded.summary


def test_service_rejects_model_requested_tool_hidden_from_planner(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    target = config.workspace_root / "owned.txt"
    responses = iter(
        [
            ActionResult(
                True,
                '{"action":"tool_call","tool_name":"write_file","arguments":{"path":"owned.txt","content":"owned"}}',
            ),
            ActionResult(
                True,
                '{"action":"answer","answer":"I cannot write files from the chat planner. <END_OF_MESSAGE>"}',
            ),
        ]
    )

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, **kwargs):
        return next(responses)

    service.ollama.ask = mock_ask
    result = service.handle("Write owned.txt")
    assert result.ok is True
    assert not target.exists()
    rejected = result.tool_calls[0]
    assert rejected.tool_name == "write_file"
    assert rejected.ok is False
    assert "not available to the chat planner" in rejected.summary
    assert "write_file" not in rejected.data["available_tools"]


def test_service_blocks_confirmation_gated_planner_tool_without_confirm(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    target = config.workspace_root / "owned.txt"
    responses = iter(
        [
            ActionResult(
                True,
                '{"action":"tool_call","tool_name":"shell_command","arguments":{"command":"python -c \\\"open(\'owned.txt\', \'w\').write(\'owned\')\\\""}}',
            ),
            ActionResult(
                True,
                '{"action":"answer","answer":"Confirmation is required. <END_OF_MESSAGE>"}',
            ),
        ]
    )

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, **kwargs):
        return next(responses)

    service.ollama.ask = mock_ask
    result = service.handle("Run a shell command")
    assert result.ok is True
    assert not target.exists()
    blocked = result.tool_calls[0]
    assert blocked.tool_name == "shell_command"
    assert blocked.ok is False
    assert blocked.data["requires_confirmation"] is True


def test_service_runs_confirmation_gated_planner_tool_with_confirm(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    responses = iter(
        [
            ActionResult(
                True,
                '{"action":"tool_call","tool_name":"shell_command","arguments":{"command":"python -c \\\"print(123)\\\""}}',
            ),
            ActionResult(
                True,
                '{"action":"answer","answer":"The command printed 123. <END_OF_MESSAGE>"}',
            ),
        ]
    )

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None, **kwargs):
        return next(responses)

    service.ollama.ask = mock_ask
    result = service.handle("Run a shell command", confirm=True)
    assert result.ok is True
    shell_call = result.tool_calls[0]
    assert shell_call.tool_name == "shell_command"
    assert shell_call.ok is True
    assert shell_call.summary.strip() == "123"


def test_service_autonomous_execution_loop(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)

    def mock_ask(prompt, system_prompt=None, response_format=None):
        return ActionResult(
            True,
            '{"type":"answer","message":"Step completed. <END_OF_MESSAGE>"}',
        )

    service.ollama.ask = mock_ask
    result = service.run_autonomous("test goal", max_steps=2)
    assert result.ok is True
    assert "test goal" in result.message or "completed" in result.message.lower()
    status = service.tools.get_task_status(result.tool_calls[0].data["task_id"])
    assert status.ok is True
    assert status.data["status"] == "completed"
    assert len(status.data["steps"]) == 2


def test_service_autonomous_with_tool_calls(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)

    responses = iter(
        [
            ActionResult(
                True,
                '{"type":"tool_call","tool_name":"file_search","arguments":{"query":"README"}}',
            ),
            ActionResult(
                True,
                '{"type":"answer","message":"Found files. <END_OF_MESSAGE>"}',
            ),
        ]
    )

    def mock_ask(prompt, system_prompt=None, response_format=None):
        return next(responses)

    service.ollama.ask = mock_ask
    result = service.run_autonomous("find readme", max_steps=1)
    assert len(result.tool_calls) >= 2
    read_calls = [call for call in result.tool_calls if call.tool_name == "file_search"]
    assert len(read_calls) == 1


def test_service_loops_until_end_marker_is_present(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    responses = iter(
        [
            ActionResult(
                True,
                '{"type":"answer","message":"Almost done."}',
            ),
            ActionResult(
                True,
                '{"type":"answer","message":"Actually done. <END_OF_MESSAGE>"}',
            ),
        ]
    )

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None):
        return next(responses)

    service.ollama.ask = mock_ask
    result = service.handle("What does README.md say?")
    assert result.ok is True
    assert result.message == "Actually done."


def test_service_answers_directly_from_contextual_web_search(tmp_path: Path):
    config = make_config(tmp_path)
    config.ollama.enabled = True
    service = ShowcaseService(config)
    service.tools.maybe_contextual_tool_calls = lambda text: [
        ToolCall(
            "web_search",
            True,
            "CLI - AGS Wiki: Toggle Window -- toggle-window (https://aylur.github.io/ags-docs/config/cli/)",
        )
    ]
    calls = []

    def mock_ask(prompt, system_prompt=None, response_format=None, model=None):
        calls.append(response_format)
        return ActionResult(
            True,
            "The AGS docs mention toggle-window in the CLI docs at https://aylur.github.io/ags-docs/config/cli/. <END_OF_MESSAGE>",
        )

    service.ollama.ask = mock_ask
    result = service.handle("What do the official AGS docs say is the toggle window command?")
    assert result.ok is True
    assert result.tool_calls[0].tool_name == "web_search"
    assert result.message.startswith("The AGS docs mention")
    assert calls == [None]


def test_service_prompt_includes_current_date_context(tmp_path: Path):
    config = make_config(tmp_path)
    service = ShowcaseService(config)
    prompt = service._build_tool_choice_prompt(
        "latest linux kernel stable version",
        "fallback",
        ["web_search"],
        [],
        [],
        [],
    )
    assert "Current date:" in prompt


def test_service_autonomous_handles_planning_failure(tmp_path: Path):
    runtime = make_runtime(tmp_path)
    task_path = runtime.task_path
    task_path.parent.mkdir(parents=True, exist_ok=True)

    tasks = {
        "bad-id": {
            "title": "fail",
            "status": "planned",
            "steps": [],
            "created_at": "now",
            "updated_at": "now",
        }
    }
    runtime._save_json(task_path, tasks)

    result = runtime.execute_step("bad-id", 0)
    assert result.ok is False
    assert "out of range" in result.summary.lower()
