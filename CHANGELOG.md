# Changelog

All notable changes to this project will be documented here.

## Unreleased

### Added

- CI workflow for Python install/tests, compile checks, shell syntax checks, and frontend JavaScript syntax checks.
- Release-facing installation, configuration, tools, troubleshooting, safety, and release-checklist docs.
- Release checklist script for local validation and tracked-artifact checks.

### Changed

- Web UI and Ollama-compatible wrapper now bind to `127.0.0.1` by default; LAN exposure requires an explicit `--host 0.0.0.0`.
- Tool metadata now marks planner-visible tools as `stable` and runtime-only tools as `experimental`.
- Browser local-storage schema is documented and recorded with `showcase.ui.schema.v1`.

## v1.0.0 Planning

Expected breaking changes from the alpha line before `v1.0.0`:

- Browser local-storage keys and session shapes may be consolidated one final time before being treated as stable.
- Tool names and planner-visible schemas may be narrowed to a documented stable set.
- Default network binding remains loopback-only; deployments that relied on implicit LAN binding must pass `--host 0.0.0.0` explicitly.
- Benchmark result formats under `state/model_benchmarks.json` may change while benchmark categories are finalized.

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
