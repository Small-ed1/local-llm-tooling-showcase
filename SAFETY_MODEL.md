# Safety Model

This project reduces accidental model access to local capabilities, but it is not a sandbox.

## Planner Boundary

- The model planner only sees schemas in `src/tooling_showcase/tool_protocol.py`.
- Runtime tools without planner schemas are experimental and manual by default.
- Shell execution is visible but not safe for automatic execution and remains confirmation-gated for risky commands.

## Network Boundary

- `serve` and `serve-ollama` bind to `127.0.0.1` by default.
- Use `--host 0.0.0.0` only for intentional LAN exposure.

## State Boundary

- Browser state is local storage.
- Backend state is ignored under `state/`.
- Do not store secrets in prompts, memories, examples, benchmark tasks, or screenshots.

Run `tooling-showcase doctor` before release-facing checks and inspect release archives before publishing.
