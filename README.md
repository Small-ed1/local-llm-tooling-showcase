# Local LLM Tooling Showcase

`local-llm-tooling-showcase` is a compact, runnable demo that pulls the strongest tooling ideas out of the existing workspace and presents them as one clean local-first assistant runtime.

It is intentionally pitched as a showcase, not a giant platform:

- deterministic command routing first
- structured local tools second
- workspace adapters for source-project provenance third
- local Ollama reasoning fourth
- immutable event logging throughout

## What It Showcases

This project consolidates the best tooling patterns from the surrounding repos:

- `autonomous-research-station`
  - direct tool-style execution surfaces
  - lightweight local retrieval and indexing
  - local-first Ollama usage
- `northstar`
  - deterministic command routing before LLM fallback
  - concise tool catalog conditioning for the model
  - operator-friendly CLI shape
- `behavioral-os`
  - clean service boundary and context injection mindset
  - explicit runtime result models instead of vague chat glue
- `mini-arena-social-simulation`
  - immutable event journaling
  - strict structured actions instead of freeform hidden behavior

## Core Flow

1. Route obvious requests to concrete tools.
2. Execute a bounded local tool when possible.
3. Log the request, route, tool calls, and response as an immutable event.
4. If no direct route is enough, select relevant tool docs and gathered context.
5. Ask a local Ollama model for the final response.

## Included Tooling

- file search
- file read
- content search
- lightweight local index build/query
- simple web search
- guarded shell execution
- workspace adapter inventory
- Ollama fallback with tool-aware prompts

## Showcase Extras

- stdlib web UI with live requests, adapter cards, and journal feed
- workspace adapters that detect and summarize source repos
- stronger shell safety policy with blocked and confirm-required commands
- CLI commands for `adapters` and `serve`

## Quick Start

```bash
cd /home/small_ed/Projects/local-llm-tooling-showcase
python -m venv .venv
. .venv/bin/activate
pip install -e .
tooling-showcase ask "find file README"
tooling-showcase ask "read file README.md"
tooling-showcase ask "search content tool_name"
tooling-showcase ask "search web for ollama structured outputs"
tooling-showcase ask "how should I compare local LLM tool runtimes?"
tooling-showcase adapters
tooling-showcase serve
```

If Ollama is running locally, open-ended questions use it automatically. If not, the direct tools still work and the fallback stays explicit.

## Example Commands

```bash
tooling-showcase ask "build an index for this project"
tooling-showcase ask "query the index for routing and tool catalog"
tooling-showcase ask "show adapters"
tooling-showcase ask "run git status" --confirm
tooling-showcase ask "how does the showcase choose tools?"
tooling-showcase journal --limit 5
```

## Ollama-Compatible Wrapper

You can expose the showcase as an Ollama-compatible endpoint for apps that expect the Ollama API.

```bash
./start-servers.sh
```

Default endpoints:

- showcase web/API: `http://127.0.0.1:8123`
- raw Ollama: `http://127.0.0.1:11434`
- tool-capable Ollama wrapper: `http://127.0.0.1:11436`

For a Tailnet-hosted machine, point your client app at:

```text
http://<tailnet-ip>:11436
```

The wrapper accepts standard Ollama-style `/api/chat` and `/api/generate` requests, forwards other Ollama endpoints upstream, and runs showcase tools when they help answer the request.

## Why This Exists

The workspace already had strong pieces, but they were split across separate projects:

- one had the best tool runtime
- one had the best user-facing fallback pattern
- one had the best service boundary discipline
- one had the best structured event logging mindset

This repo turns that into one small, inspectable showcase you can extend instead of just reviewing in pieces.
