# Troubleshooting

## Ollama Is Unavailable

Symptoms: model list shows offline, open-ended answers say local Ollama fallback is disabled/unreachable, or `/api/models` returns an error.

Checks:

```bash
ollama list
curl http://127.0.0.1:11434/api/tags
tooling-showcase ask "find file README"
```

Deterministic local routes such as file search can still work without Ollama. Open-ended answers and benchmarking require Ollama.

## Benchmark Fails Or Is Slow

Benchmarking contacts every selected local model and can take a long time.

Use a smoke run:

```bash
tooling-showcase benchmark --limit-tasks 2
```

Default behavior benchmarks only unprofiled models. Use `--all` only when intentionally rebuilding all profiles. Failed benchmark inventory should not break `./install.sh`; it prints a message and continues.

## Web UI Does Not Load

Default bind is loopback:

```bash
tooling-showcase serve --host 127.0.0.1 --port 8123
```

Then open `http://127.0.0.1:8123`. For LAN testing, explicitly pass `--host 0.0.0.0` and review `SAFETY.md` first.

## Tool Was Rejected

Common reasons:

- The tool exists in `ToolRuntime` but is not listed in `tool_protocol.py`.
- The tool requires confirmation, especially `shell_command`.
- The model invented a tool name.

Use the Manual Tool Console or `tests/test_service.py` patterns to verify exact tool names and arguments.

## Local State Looks Wrong

Browser UI state is local storage. Backend state is under ignored `state/`.

Safe reset options:

- Use Settings -> Data to clear browser UI state.
- Remove specific ignored state files under `state/` only when you understand what they store.
- Do not commit `state/`, benchmark outputs, logs, or event journals.
