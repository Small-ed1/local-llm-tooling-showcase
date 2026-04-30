# Configuration

## Hosts And Ports

Both server commands bind to loopback by default.

```bash
tooling-showcase serve --host 127.0.0.1 --port 8123
tooling-showcase serve-ollama --host 127.0.0.1 --port 11436
```

Use LAN binding only when intentional:

```bash
tooling-showcase serve --host 0.0.0.0 --port 8123
tooling-showcase serve-ollama --host 0.0.0.0 --port 11436
```

`./start-servers.sh` starts both services on `127.0.0.1`, writes logs under `state/logs/`, and exports `PYTHONPATH=src`.

## Environment Variables

- `TOOLING_SHOWCASE_WORKSPACE`: workspace inspected by tools, default repo root.
- `TOOLING_SHOWCASE_PORTFOLIO`: parent workspace used for adapter discovery, default repo parent.
- `TOOLING_SHOWCASE_JOURNAL`: event journal path, default `state/events.jsonl`.
- `TOOLING_SHOWCASE_BENCHMARKS`: benchmark profile path, default `state/model_benchmarks.json`.
- `TOOLING_SHOWCASE_OLLAMA_ENDPOINT`: chat endpoint, default `http://127.0.0.1:11434/api/chat`.
- `TOOLING_SHOWCASE_OLLAMA_MODEL`: fallback model, default `qwen3:8b`.
- `TOOLING_SHOWCASE_OLLAMA_TIMEOUT`: Ollama request timeout seconds, default `120`.
- `TOOLING_SHOWCASE_OLLAMA_TEMPERATURE`: default model temperature, default `0.2`.
- `TOOLING_SHOWCASE_OLLAMA_ENABLED`: set `false` to disable Ollama fallback.
- `SHOWCASE_LIBRARY_PATHS`: colon-separated local EPUB/ZIM/library roots.

## Browser Local Storage

The UI currently uses schema version `3` and records it at `showcase.ui.schema.v1`.

Current keys:

- `showcase.ui.sessions.v3`
- `showcase.ui.activeSession.v3`
- `showcase.ui.memories.v3`
- `showcase.ui.settings.v3`
- `showcase.ui.systemPrompt.v3`
- `showcase.ui.systemPrompts.v1`
- `showcase.ui.activeSystemPrompt.v1`
- `showcase.ui.profile.v1`

Legacy `v2` sessions, active session, memories, and system prompt are imported in `loadLocalState()`.
