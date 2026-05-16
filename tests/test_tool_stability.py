from pathlib import Path

from tooling_showcase.catalog import TOOL_DOC_BY_ID
from tooling_showcase.config import OllamaConfig, ShellPolicy, ShowcaseConfig
from tooling_showcase.server import _tool_cards
from tooling_showcase.service import ShowcaseService
from tooling_showcase.tool_protocol import TOOL_SCHEMAS, visible_tool_schemas
from tooling_showcase.tools import ToolRuntime


def test_tool_cards_mark_stability():
    cards = {card["id"]: card for card in _tool_cards(["read_file", "write_file", "draft_system_prompt"])}

    assert cards["read_file"]["stability"] == "stable"
    assert cards["draft_system_prompt"]["stability"] == "stable"
    assert cards["write_file"]["stability"] == "experimental"


def test_planner_visible_tool_contract_is_intentional_and_documented():
    expected = {
        "adapter_inventory",
        "build_index",
        "content_search",
        "create_memory",
        "delete_memory",
        "draft_system_prompt",
        "edit_memory",
        "expand_search_result",
        "file_search",
        "library_info",
        "library_read_epub",
        "library_read_zim",
        "library_search",
        "list_memories",
        "load_memory",
        "local_doc_read",
        "local_doc_search",
        "query_index",
        "read_file",
        "save_memory",
        "shell_command",
        "tool_structure",
        "tree_view",
        "update_memory",
        "web_search",
    }

    assert set(TOOL_SCHEMAS) == expected
    assert expected <= set(TOOL_DOC_BY_ID)


def test_memory_tool_docs_warn_against_secret_storage():
    tools_doc = Path(__file__).resolve().parents[1] / "docs" / "TOOLS.md"

    text = tools_doc.read_text(encoding="utf-8")

    assert "Memory tools" in text
    assert "Do not store secrets" in text


def make_config(tmp_path: Path) -> ShowcaseConfig:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("showcase readme", encoding="utf-8")
    return ShowcaseConfig(
        project_root=tmp_path,
        workspace_root=workspace,
        portfolio_root=tmp_path,
        journal_path=tmp_path / "state" / "events.jsonl",
        ollama=OllamaConfig(enabled=False),
        shell_policy=ShellPolicy(),
    )


def test_planner_visible_tool_surface_is_protocol_backed(tmp_path: Path):
    config = make_config(tmp_path)
    runtime = ToolRuntime(config)
    service = ShowcaseService(config)

    available = runtime.available_tools()
    expected = sorted(name for name in available if name in TOOL_SCHEMAS)
    structure = runtime.tool_structure()
    schema_names = sorted(schema["name"] for schema in visible_tool_schemas(available))
    request_context = service._prepare_request_context(
        "read README.md",
        model=None,
        options=None,
        ollama_options=None,
        messages=None,
    )

    assert structure.data["planner_visible"] == expected
    assert schema_names == expected
    assert sorted(request_context.planner_tools) == expected
    assert set(expected) <= set(TOOL_SCHEMAS)


def test_file_and_git_mutation_tools_are_not_planner_visible(tmp_path: Path):
    runtime = ToolRuntime(make_config(tmp_path))
    visible = set(runtime.tool_structure().data["planner_visible"])
    mutation_tools = {
        "append_file",
        "apply_patch",
        "copy_file",
        "create_file",
        "delete_file",
        "git_add",
        "git_branch",
        "git_checkout",
        "git_commit",
        "git_merge",
        "git_reset",
        "git_stash",
        "move_file",
        "write_file",
    }

    assert mutation_tools.isdisjoint(visible)
