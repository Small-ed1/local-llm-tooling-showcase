# Ollama Wrapper

The wrapper exposes this project's tool-capable runtime through Ollama-compatible endpoints.

## Start

```bash
tooling-showcase serve-ollama --host 127.0.0.1 --port 11436
```

Or start both services:

```bash
./start-servers.sh
```

## Endpoints

- `POST /api/chat`: handled by the showcase runtime, then returned in Ollama chat shape.
- `POST /api/generate`: handled by the showcase runtime, then returned in Ollama generate shape.
- Other paths, such as `GET /api/tags`, are proxied to the configured upstream Ollama base URL.

## Curl Smoke Test

```bash
curl -s http://127.0.0.1:11436/api/tags
curl -s http://127.0.0.1:11436/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"showcase-wrapper","stream":false,"messages":[{"role":"user","content":"find file README"}]}'
```

Use `TOOLING_SHOWCASE_OLLAMA_ENABLED=false` when you want deterministic routes without model fallback.
