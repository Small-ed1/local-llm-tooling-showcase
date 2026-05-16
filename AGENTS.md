# AGENTS.md

## Setup And Checks

- Use Python 3.11+. Preferred setup is `./install.sh` from repo root; it can create `.venv`, install `.[dev]`, run tests/static JS checks, and prompt to benchmark when more than 3 Ollama models are installed.
- Manual setup: `python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]' && tooling-showcase doctor`.
- If the package is not installed in the current shell, run CLI probes with `PYTHONPATH=src`, e.g. `PYTHONPATH=src python -m tooling_showcase.cli benchmark --list-models`.
- Release gate: `scripts/release-check.sh` from repo root. It runs whitespace, all three static JS syntax checks, Python compile, shell syntax, `PYTHONPATH=src python -m tooling_showcase.cli doctor`, `pytest tests/`, optional `ruff`, and tracked-artifact guards.
- Focused checks: `pytest tests/test_service.py tests/test_tool_stability.py tests/test_tools.py`, `pytest tests/test_service.py::test_service_allows_model_memory_tools`, `pytest tests/test_static_ui.py`, `pytest tests/test_browser_smoke.py`, `python -m ruff check src tests`.
- Static UI syntax check is three files in order: `node --check src/tooling_showcase/static/app-data.js`, `node --check src/tooling_showcase/static/markdown.js`, `node --check src/tooling_showcase/static/app.js`.
- CI runs Python 3.11-3.14 with Node 22, dev install, doctor, whitespace/shell/compile/static JS/pytest/ruff, wheel build, wheel install, and a separate Playwright Chromium browser smoke job; local browser smoke skips if Playwright/Chromium is missing.

## Runtime Entrypoints

- Console script: `tooling-showcase` from `pyproject.toml`; subcommands include `ask`, `journal`, `adapters`, `models`, `benchmark`, `doctor`, `tui`, `serve`, `serve-ollama`, and `research`.
- Web UI/API: `tooling-showcase serve --host 127.0.0.1 --port 8123`. Manual `/api/tool` is disabled on non-loopback binds unless `--enable-remote-tool-api` or `TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API=1` is set.
- Ollama-compatible wrapper: `tooling-showcase serve-ollama --host 127.0.0.1 --port 11436 --ollama-endpoint http://127.0.0.1:11434/api/chat`.
- `./start-servers.sh` starts both loopback services, exports `PYTHONPATH=src`, logs to ignored `state/logs/`, and uses `SHOWCASE_SERVER_PORT`, `SHOWCASE_WRAPPER_PORT`, and `SHOWCASE_OLLAMA_ENDPOINT` for overrides.
- Useful CLI probes: `tooling-showcase ask "find file README"`, `tooling-showcase journal --limit 5`, `tooling-showcase adapters`, `tooling-showcase models`, `tooling-showcase benchmark --list-models`.

## Architecture Notes

- `ShowcaseService` in `service.py` composes mixins: `service_request.py` builds request/model/tool context, `service_fallbacks.py` handles deterministic and no-Ollama direct tools, `service_planner.py` runs the model-planned tool loop, and `service_streaming.py` mirrors `handle()` for streaming.
- Default planner budget is `max_tool_calls=4`; autonomous runs use `max_tool_calls_per_step=3`.
- `router.py` handles clean deterministic intents before Ollama fallback.
- `tools.py` owns `ToolRuntime`, state paths, `available_tools()`, shell safety, memory storage, adapters, library access, and runtime tool implementations. Tools in `MANUAL_CONFIRMATION_TOOLS` require `confirm=true`.
- `tool_protocol.py` is the planner-visible allowlist. Adding a `ToolRuntime` method creates a runtime/manual tool only; add `catalog.py` docs, tests, and a schema only when the model planner may call it.
- `model_routing.py` contains fallback static model categories; `benchmarking.py` writes local profiles to `state/model_benchmarks.json`, and benchmarked profiles override auto-routing when present.
- `server.py` is a stdlib HTTP server. Static UI source is `src/tooling_showcase/static/`, has no build step, and `index.html` loads `app-data.js` before `markdown.js` before `app.js`.
- `src/tooling_showcase/research/` backs `tooling-showcase research` and `/api/research`; sessions and reports are ignored under `state/research/`.

## State, Environment, And Safety

- Ignored local state lives under `state/`: journal, memories, benchmark results, logs, research sessions/reports, indexes, tasks, and tool stats. Do not commit it.
- Config env vars: `TOOLING_SHOWCASE_WORKSPACE`, `TOOLING_SHOWCASE_PORTFOLIO`, `TOOLING_SHOWCASE_JOURNAL`, `TOOLING_SHOWCASE_BENCHMARKS`, `TOOLING_SHOWCASE_OLLAMA_*`, `TOOLING_SHOWCASE_TOOL_TIMEOUT`, `TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API`, and `SHOWCASE_LIBRARY_PATHS`.
- Set `TOOLING_SHOWCASE_OLLAMA_ENABLED=false` for deterministic routes without model fallback; Ollama is still required for open-ended answers and benchmarking.
- Shell policy blocks `sudo`, `rm -rf /`, `mkfs`, `dd if=`, `shutdown`, `reboot`, `> /dev/sd`, and `chmod -R 777 /`; risky `rm`/`mv`/`cp`/`kill`/redirect/git clean/reset patterns require confirmation.
- Memory tools are planner-visible but intended only for explicit stable memory requests. Model-created memories persist in `state/memories.json`; do not store secrets there.
- The benchmark command contacts local Ollama and can be slow. Use `--limit-tasks` for smoke runs, and remember default benchmarking only covers unprofiled models unless `--all` is passed.

## Release And Asset Gotchas

- Version/release status is checked in `pyproject.toml`, `src/tooling_showcase/__init__.py`, `README.md`, and `tests/test_release_docs.py`; keep them in sync when cutting a release.
- Static UI package data is declared in `pyproject.toml`; if new static subdirectories are added, verify they are included in source archives.
- Screenshot assets live in `docs/screenshots/desktop/` and `docs/screenshots/mobile/`. Keep `.gitignore` root-anchored as `/desktop/`; an unanchored `desktop/` pattern hides desktop screenshot assets.
- Current clean source zips are made with `git archive --format=zip --prefix="local-llm-tooling-showcase-<tag>/" --output="dist/local-llm-tooling-showcase-<tag>.zip" <tag>`.
- Before publishing a release archive, inspect for required docs/screenshots/static assets and blocked local artifacts such as `state/`, `.venv/`, `.ruff_cache/`, `showcase_ui_bundle/`, `model_live_note.txt`, `add_library_tools.py`, and `showcase_static_ui_patch.zip`.
