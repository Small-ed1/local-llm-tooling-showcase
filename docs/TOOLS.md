# Tools

Runtime tools live in `ToolRuntime` (`src/tooling_showcase/tools.py`). Planner-visible tools are only the tools with schemas in `src/tooling_showcase/tool_protocol.py`.

## Stable Planner Tools

These are the tools exposed by `tool_protocol.py`. `shell_command` is visible but not safe for automatic execution; risky shell commands still require confirmation.

- `adapter_inventory`
- `build_index`
- `content_search`
- `create_memory`
- `delete_memory`
- `draft_system_prompt`
- `edit_memory`
- `expand_search_result`
- `file_search`
- `library_info`
- `library_read_epub`
- `library_read_zim`
- `library_search`
- `list_memories`
- `load_memory`
- `query_index`
- `read_file`
- `save_memory`
- `shell_command` with confirmation rules
- `tree_view`
- `update_memory`
- `web_search`

## Experimental Runtime Tools

Everything else in `ToolRuntime.available_tools()` is available for manual/runtime experiments but should not be assumed planner-safe. Examples include file mutation, git mutation, optional audio/image/device tools, task helpers, indexing maintenance, and telemetry helpers.

## Safety Rules

- Shell execution blocks known destructive patterns and requires confirmation for risky substrings.
- File write/delete/git mutation tools are intentionally not planner-visible by default.
- Memory tools should only store explicit, stable user preferences or facts. Do not store secrets.

## Adding A Tool

1. Add the `ToolRuntime` method.
2. Add catalog docs in `catalog.py` if it should be discoverable.
3. Add a schema in `tool_protocol.py` only if the model planner may call it.
4. Add or update tests for direct runtime behavior and planner visibility.
