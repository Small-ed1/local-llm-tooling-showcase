# AGENTS.md

## Setup And Checks

- Preferred setup: `./install.sh` from repo root. It can create `.venv`, install editable, run tests, run `node --check`, and prompt for benchmarks when more than 3 Ollama models are installed.
- Manual setup: `python -m venv .venv && . .venv/bin/activate && pip install -e .`.
- Full local verification before release-facing changes: `git diff --check`, `node --check src/tooling_showcase/static/app.js`, `python -m compileall -q src tests`, `bash -n install.sh && bash -n start-servers.sh`, `pytest tests/`.
- Focused tests work normally, e.g. `pytest tests/test_service.py::test_service_allows_model_memory_tools` or `pytest tests/test_static_ui.py`.
- If the package is not installed in the current shell, run CLI smoke checks with `PYTHONPATH=src`, e.g. `PYTHONPATH=src python -m tooling_showcase.cli benchmark --list-models`.
- CI runs Python install/tests, compile checks, shell syntax checks, and `node --check`; local checks remain the release gate before publishing.

## Runtime Entrypoints

- Console script: `tooling-showcase` from `pyproject.toml`.
- Web UI/API: `tooling-showcase serve --host 127.0.0.1 --port 8123`; static UI source is `src/tooling_showcase/static/`.
- Ollama-compatible wrapper: `tooling-showcase serve-ollama --host 127.0.0.1 --port 11436 --ollama-endpoint http://127.0.0.1:11434/api/chat`.
- `./start-servers.sh` starts both services path-relative, exports `PYTHONPATH=src`, and logs to ignored `state/logs/`.
- Useful CLI probes: `tooling-showcase ask "find file README"`, `tooling-showcase journal --limit 5`, `tooling-showcase adapters`, `tooling-showcase models`, `tooling-showcase benchmark --list-models`.

## Architecture Notes

- `service.py` is the orchestration point: deterministic routing, optional direct fallback, model-planned tool loop, and event logging. Default planner budget is `max_tool_calls=4`.
- `router.py` handles clean deterministic intents before LLM fallback.
- `tools.py` owns `ToolRuntime`, state paths, local tool implementations, shell safety, memory storage, and adapter/library access.
- `tool_protocol.py` is the planner-visible allowlist. Adding a runtime tool does not expose it to models unless it has a schema there.
- `model_routing.py` contains fallback static model categories; `benchmarking.py` derives local model profiles in `state/model_benchmarks.json`, and benchmarked profiles override auto-routing when present.
- `server.py` is a stdlib HTTP server; there is no frontend build step. Validate frontend edits with `node --check src/tooling_showcase/static/app.js`.

## State, Environment, And Safety

- Ignored local state lives under `state/`: journal, memories, benchmark results, logs, screenshots, and tool stats. Do not commit it.
- Important env vars: `TOOLING_SHOWCASE_WORKSPACE`, `TOOLING_SHOWCASE_PORTFOLIO`, `TOOLING_SHOWCASE_JOURNAL`, `TOOLING_SHOWCASE_BENCHMARKS`, `TOOLING_SHOWCASE_OLLAMA_ENDPOINT`, `TOOLING_SHOWCASE_OLLAMA_MODEL`, `TOOLING_SHOWCASE_OLLAMA_TIMEOUT`, `TOOLING_SHOWCASE_OLLAMA_TEMPERATURE`, `TOOLING_SHOWCASE_OLLAMA_ENABLED`, `SHOWCASE_LIBRARY_PATHS`.
- Shell policy blocks `sudo`, `rm -rf /`, `mkfs`, `dd if=`, `shutdown`, `reboot`, `> /dev/sd`, and `chmod -R 777 /`; risky shell substrings require confirmation.
- Memory tools are planner-visible only for explicit user memory requests. Model-created memories persist in `state/memories.json`; do not store secrets there.
- The benchmark command contacts local Ollama and can be slow. Use `--limit-tasks` for smoke runs, and remember default benchmarking only covers unprofiled models unless `--all` is passed.

## Release And Asset Gotchas

- Version is duplicated in `pyproject.toml` and `src/tooling_showcase/__init__.py`; keep them in sync when cutting a release.
- Static UI package data is declared in `pyproject.toml`; if new static subdirectories are added, verify they are included in source archives.
- Screenshot assets live in `docs/screenshots/desktop/` and `docs/screenshots/mobile/`. Keep `.gitignore` root-anchored as `/desktop/`; an unanchored `desktop/` pattern hides desktop screenshot assets.
- Current clean source zips are made with `git archive --format=zip --prefix="local-llm-tooling-showcase-<tag>/" --output="dist/local-llm-tooling-showcase-<tag>.zip" <tag>`.
- Before publishing a GitHub release, inspect the archive for required files and blocked local artifacts such as `state/`, `.venv/`, `.ruff_cache/`, `showcase_ui_bundle/`, `model_live_note.txt`, `add_library_tools.py`, and `showcase_static_ui_patch.zip`.
