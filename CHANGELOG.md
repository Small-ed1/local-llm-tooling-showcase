# Changelog

All notable changes to this project will be documented here.

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
