# AGENTS.md

## Quick Commands

```bash
# Setup
python -m venv .venv && . .venv/bin/activate && pip install -e .

# Direct CLI
tooling-showcase ask "find file AGENTS"        # Route through runtime
tooling-showcase journal --limit 5        # Show event log
tooling-showcase adapters                 # Show workspace adapters
tooling-showcase models                  # Show model profiles
tooling-showcase serve                 # Web UI (port 8123)
tooling-showcase serve-ollama        # Ollama-compatible API (port 11436)

# Run tests
pytest tests/
```

## Architecture

- **router.py**: Deterministic `IntentRouter` routes clean requests to tools before LLM fallback
- **service.py**: `ShowcaseService` orchestrates routing → tool execution → LLM fallback loop (max 8 steps)
- **tools.py**: `ToolRuntime` implements all tools (file ops, git, shell, web search, weather, indexing, etc.)
- **ollama_wrapper.py**: Exposes showcase via Ollama-compatible API (port 11436)

## Shell Safety

Risky commands blocked: `sudo`, `rm -rf /`, `mkfs`, `dd if=`, `shutdown`, `reboot`, `> /dev/sd`, `chmod -R 777 /`
Confirmation required for: `rm`, `mv`, `cp`, `>`, `>>`, `git clean`, `git reset`, `pkill`, `kill`

## Environment Variables

- `TOOLING_SHOWCASE_WORKSPACE`: Sandbox root (default: project root)
- `TOOLING_SHOWCASE_PORTFOLIO`: Parent workspace for adapters
- `TOOLING_SHOWCASE_OLLAMA_MODEL`: Default model (default: qwen3:8b)
- `TOOLING_SHOWCASE_OLLAMA_TIMEOUT`: Request timeout (default: 120s)
- `SHOWCASE_LIBRARY_PATHS`: Local book library paths (colon-separated, colon-defaults to ~/Books:~/ebooks:~/Kiwix:~/zims)

## Model Routing

Task-specific models selected via `model_routing.py`. Override with `--model` flag in CLI or pass to `service.handle()`.