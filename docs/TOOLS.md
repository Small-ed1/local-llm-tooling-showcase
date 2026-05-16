# Tools

Runtime tools live in `ToolRuntime` (`src/tooling_showcase/tools.py`). Planner-visible tools are only the tools with schemas in `src/tooling_showcase/tool_protocol.py`.

`tooling-showcase doctor` is a CLI health check, not a planner-visible runtime tool.

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
- `local_doc_search`
- `local_doc_read`
- `list_memories`
- `load_memory`
- `query_index`
- `read_file`
- `save_memory`
- `shell_command` with confirmation rules
- `tool_structure`
- `tree_view`
- `update_memory`
- `web_search`

## Experimental Runtime Tools

Everything else in `ToolRuntime.available_tools()` is available for manual/runtime experiments but should not be assumed planner-safe. Examples include file mutation, git mutation, optional audio/image/device tools, task helpers, indexing maintenance, telemetry helpers, and confirmation-gated documentation edits such as `local_doc_replace`.

## Runtime Tool Tags

`tool_structure` exposes tag-based classification for every tool in `ToolRuntime.available_tools()`: `planner-safe`, `manual-only`, `mutation`, `shell`, `network`, `stateful`, and `experimental`.

`mutation` means a workspace, git, process, dependency, or arbitrary shell-wrapper action that must be present in `MANUAL_CONFIRMATION_TOOLS` and blocked until `confirm=true`. `stateful` means the tool reads or writes local showcase state such as indexes, memories, tasks, checkpoints, device-command logs, or journal entries.

## Safety Rules

- Shell execution parses common command shapes, blocks known destructive command/argument patterns, requires confirmation for risky commands, and keeps raw-pattern checks as a fallback guardrail.
- File write/delete/git mutation tools and arbitrary shell-wrapper tools are intentionally not planner-visible by default, and manual mutation tools are blocked until `confirm=true`.
- Planner-visible URL expansion rejects localhost, private/RFC1918, link-local, metadata, and other non-global IP targets unless the same tool is explicitly confirmed from the manual path.
- `local_doc_search` and `local_doc_read` are planner-visible read-only documentation helpers; `local_doc_replace` is manual and confirmation-gated.
- Memory tools should only store explicit, stable user preferences or facts. Do not store secrets.

## Adding A Tool

1. Add the `ToolRuntime` method.
2. Add catalog docs in `catalog.py` if it should be discoverable.
3. Add a schema in `tool_protocol.py` only if the model planner may call it.
4. Add or update tests for direct runtime behavior and planner visibility.
