# Showcase UI Bundle v3

Drop-in modern web UI for `local-llm-tooling-showcase`.

## What v3 adds

- Tabbed floating settings modal
  - General settings
  - Model-specific Ollama options
  - Memory settings
  - Interface settings
  - Data controls
- Model-specific controls
  - temperature
  - context tokens / `num_ctx`
  - top-p
  - top-k
  - repeat penalty
  - seed
  - max prediction / `num_predict`
  - keep-alive
  - stop sequences
  - response format / JSON mode
  - system prompt override
- Clickable detail views
  - messages
  - thinking boxes
  - tool calls
  - manual tool results
  - tools
  - adapters
  - journal events
  - sessions
  - memories
  - panels by double-click
- Rich adapter cards
  - detected path
  - file counts
  - Python/Markdown/JSON file counts
  - total bytes
  - modified time
  - created/status-changed time
  - journal mentions
  - browser message mentions
  - usage ideas
- Rich journal metadata
  - display limit setting
  - backend stats
  - event details modal
  - guarded clear action
- Data utilities
  - export current session
  - export all browser sessions/memories/settings
  - clear backend journal
  - clear browser UI state with confirmation

## Install

```bash
unzip showcase_ui_bundle_v3.zip
cd showcase_ui_bundle
./install-ui.sh /home/small_ed/Projects/local-llm-tooling-showcase
```

Then run:

```bash
cd /home/small_ed/Projects/local-llm-tooling-showcase
PYTHONPATH=src tooling-showcase serve --host 0.0.0.0 --port 8123
```

## Notes

The UI is still plain HTML/CSS/JS. No npm, no build step, no framework barnacles.

The patched `server.py` keeps the existing routes and adds/enriches:

- `GET /api/tools` now returns both `tools` and `tool_cards`
- `GET /api/adapters` returns enriched adapter cards
- `GET /api/journal?limit=50` returns events plus stats
- `GET /api/runtime` returns runtime summary metadata
- `POST /api/tool` manually runs a tool
- `POST /api/journal/clear` clears the backend journal with confirmation

Model options are sent on `/api/ask` as `options` and `response_format`. The patched server passes them through when your installed `ShowcaseService.handle()` supports those kwargs, and falls back safely on older service signatures.

## What v4 mobile adds

- Mobile-first cockpit mode below 760px wide.
- Bottom navigation for Workspace, Chat, Runtime, and Settings.
- Left drawer for model/session/memory controls.
- Right drawer for tools, adapters, and journal.
- Tap scrim or drawer close buttons to return to chat.
- Settings, detail, and confirm dialogs become bottom sheets on mobile.
- Composer, chat log, and message cards are resized for touch and iPhone safe areas.
- Input font size is kept mobile-friendly to avoid iOS zoom-jump behavior.

Install command is the same, just use `showcase_ui_bundle_v4_mobile.zip`.
