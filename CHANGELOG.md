# Changelog

All notable changes to this project will be documented here.

## Unreleased

## v1.0.0 - 2026-05-16

### Added

- Consumer-first README flow with Ollama installation, default model pull, Linux/macOS/Windows setup, model tips, troubleshooting, refreshed screenshots, release package notes, and next-step direction.
- CI workflow and release gate for Python install/tests, compile checks, shell syntax checks, frontend JavaScript syntax checks, `doctor`, lint, wheel install, and browser smoke coverage.
- `tooling-showcase doctor` for install, path, static asset, state, Node, optional dev tooling, and Ollama reachability checks.
- `/api/chat` as a first-class server alias for `/api/ask`, with streaming, chat options, timeout settings, and tool calls enabled by default.
- Runtime status metadata for configured workspace, portfolio root, journal path, benchmark path, Ollama status, manual tool API status, and doctor guidance.
- Tool-surface classification tags for planner-safe, manual-only, mutation, shell, network, stateful, and experimental tools.
- Planner/tool regression coverage for tool visibility, duplicate-call suppression, invalid JSON recovery, memory intent boundaries, max-tool-call caps, SSRF URL blocks, shell safety, and runtime/manual tool contracts.
- Release-facing installation, configuration, wrapper, tools, benchmarking, troubleshooting, safety-model, contributing, and release-checklist docs.
- `MANIFEST.in` so source distributions include source code, tests, docs, screenshots, examples, Linux/Windows installers, startup scripts, and release scripts.

### Changed

- Web UI and Ollama-compatible wrapper now bind to `127.0.0.1` by default; LAN exposure requires an explicit `--host 0.0.0.0`.
- Manual `/api/tool` is disabled on non-loopback binds unless `--enable-remote-tool-api` or `TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API=1` is set.
- Tool metadata now marks planner-visible tools as `stable`, runtime-only tools as `experimental`, and mutation/shell wrappers as confirmation-gated.
- The planner prompt now prefers local docs for project documentation, web search for current/release facts, and memory tools only for explicit remember/recall/forget requests.
- Static UI status surfaces now distinguish Ollama disabled, unreachable, timeout, benchmark-missing, tool-timeout, remote manual-tool API, and research failure states with actionable next steps.
- The Ollama-compatible wrapper preserves direct single-user tool requests while still adding recent conversation context when available.
- Research failures now record failed stages and recoverable next actions.
- Windows installer now runs tests, optional static JS syntax checks, `tooling-showcase doctor`, and an Ollama inventory probe after installing `.[dev]`.
- Browser local-storage schema is documented and recorded with `showcase.ui.schema.v1`.
- Package version is promoted from the alpha line to `1.0.0`.

### Packaging

- Source release archives include `install.sh`, `install-windows.ps1`, `start-servers.sh`, `scripts/`, `docs/`, screenshots, examples, tests, and package static files.
- Wheel release includes console scripts and all static UI package assets.
- Release validation uses a temporary Ruff cache by default so ignored local `.ruff_cache` permissions do not break the gate.
- Release validation optionally parses `install-windows.ps1` with PowerShell when `pwsh` is available.

### Breaking Changes

- `tooling-showcase serve` and `tooling-showcase serve-ollama` no longer bind to all interfaces by default. Use `--host 0.0.0.0` only for intentional LAN exposure.
- Manual `/api/tool` access on non-loopback binds now requires explicit trusted-network opt-in.
- The documented stable tool contract is the planner-visible schema set in `tool_protocol.py`; runtime-only tools should be treated as experimental.
- Browser local-storage schema is versioned at `showcase.ui.schema.v1` with current schema version `3`.
- Release validation now expects Node for the static JavaScript syntax check and Python build tooling for wheel verification.

### Migration Notes

- Replace implicit LAN startup commands with `tooling-showcase serve --host 0.0.0.0` or `tooling-showcase serve-ollama --host 0.0.0.0` when LAN access is required.
- Pass `--enable-remote-tool-api` or set `TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API=1` only when exposing manual `/api/tool` on a trusted non-loopback network.
- Run `tooling-showcase doctor` after upgrading to verify paths, static assets, local state, and optional Ollama reachability.
- Browser data from the `v2` UI keys is imported by `loadLocalState()` into the current `v3` keys.
- Keep ignored `state/` data out of release archives; benchmark profiles and memories can be copied intentionally if you need to preserve local behavior.

## v0.1.0-alpha.4 - 2026-04-29

### Added

- Interactive `install.sh` setup flow with optional editable install, tests, frontend syntax checks, and benchmark prompts.
- Local Ollama benchmark suite with category scoring for context use, summarization, coding, debugging, reasoning, Linux triage, structured output, safety, planning, writing, extraction, roleplay, and retrieval.
- Benchmark-derived model profiles that stay hidden until local benchmark results exist.
- Planner-visible memory create/edit/delete/list/load support for explicit user memory requests.
- Help page covering Ollama, interface, sessions, tools, adapters, journal, settings, install, and benchmarking issues.
- Desktop and mobile screenshot assets for README and release pages.

### Changed

- Auto-routing uses benchmark-derived profiles when available.
- Mobile chat layout is narrower and more defensive against horizontal overflow.
- Sidebar now includes clearer branding, labeled quick actions, and recent session history.
- Response source drawers hotlink web source titles and URLs.
- Settings button now toggles the settings modal instead of acting only as an opener.
- Mobile sidebar trigger is a centered edge arrow instead of a top-left text button.

## v0.1.0-alpha.2 - 2026-04-29

### Changed

- Cleaned the release tree by removing temporary local artifacts and duplicate UI bundles.
- Moved optional sample assets and the Hyprland integration under `examples/`.
- Added release hygiene metadata, security notes, and path-relative startup scripts.

## v0.1.0-alpha.1 - 2026-04-29

### Added

- First alpha release of the local-first LLM tooling showcase.
- Chat UI with sessions, message editing, retry variants, source views, profile data, avatars, theme customization, and runtime status.
- Deterministic routing before LLM fallback.
- Model-directed local tool loop with duplicate-call prevention and bounded tool calls.
- Tool runtime for file search/read, content search, local indexing, web search, local library access, guarded shell commands, adapter inventory, and task helpers.
- Planner-visible tool protocol with safe auto-run metadata.
- Ollama-compatible wrapper for `/api/chat` and `/api/generate` style clients.
- Backend event journal and UI views for tools, adapters, sessions, and journal entries.

### Safety

- Shell commands are guarded, confirmation-aware, and not planner-safe by default.
- Risky and blocked command patterns are enforced by the runtime shell policy.
- Tool results and routing decisions are journaled for inspection.

### Known Limits

- Browser UI sessions, avatars, prompts, memories, and theme settings are stored in local browser storage.
- Ollama-backed open-ended answers require a running local Ollama service.
- The web UI is intentionally framework-free and still evolving quickly.
