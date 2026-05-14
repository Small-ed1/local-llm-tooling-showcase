# Safety Notes

This project is a local-first assistant runtime. It can inspect files, call tools, contact Ollama, and write local state. It is not a sandbox.

## Binding And Network Exposure

- `tooling-showcase serve` and `tooling-showcase serve-ollama` default to `127.0.0.1`.
- Use `--host 0.0.0.0` only when you intentionally want LAN access.
- Treat LAN binding as exposing local chat, tool metadata, and runtime endpoints to other devices on the network.
- The direct manual tool runner at `/api/tool` is disabled by default on non-loopback binds. Pass `--enable-remote-tool-api` or set `TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API=1` only on a trusted network when you intentionally need remote manual tool execution.

## Tool Boundaries

- The model planner only sees schemas in `src/tooling_showcase/tool_protocol.py`.
- Adding a method to `ToolRuntime` does not expose it to the planner unless a schema is added.
- Shell commands are confirmation-gated for risky executable names and blocked for known destructive command/argument patterns.
- Shell filtering uses `shlex` parsing for common command shapes plus raw-pattern fallback. It is a guardrail, not a sandbox.
- File write/delete/git mutation tools exist in the runtime but are not planner-visible by default. Manual mutation tools require explicit confirmation through a central runtime risk registry.
- Planner-visible URL expansion blocks localhost, private/RFC1918, link-local, metadata, and other non-global IP targets unless the call is explicitly confirmed from the manual tool path.

## Memory And State

- Browser sessions, UI memories, profile settings, prompts, and theme choices are stored in browser local storage.
- Model-created memories persist in `state/memories.json`.
- Benchmarks persist in `state/model_benchmarks.json`; event logs persist in `state/events.jsonl`.
- JSON state writes use lightweight per-path locks and atomic replacement for common state files, but this is still local-process coordination rather than a database.
- Do not store secrets, credentials, private keys, or sensitive personal data in prompts, memories, benchmark prompts, or examples.

## Before Public Release

- Run `scripts/release-check.sh`.
- Inspect the release zip for `state/`, `.venv/`, `.ruff_cache/`, personal paths, benchmark outputs, event journals, and temporary transfer artifacts.
- Verify screenshots do not show secrets, private paths, or private conversations.
