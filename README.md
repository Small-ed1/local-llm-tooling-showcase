# Local LLM Tooling Showcase

`local-llm-tooling-showcase` is a local-first assistant you can run on your own machine. It gives you a browser chat UI backed by local Ollama models plus guarded tools for reading files, searching code, checking docs, using web context, running research sessions, and observing what happened.

This is not a hosted SaaS product and it is not a sandbox. Run it only against folders you are comfortable exposing to local tools.

![Chat thread screenshot](docs/screenshots/desktop/chat-thread.png)

## What You Get

- A local web UI at `http://127.0.0.1:8123` with chat history, retries, variants, settings, help, tool traces, and mobile-friendly screens.
- Local file and code tools for file search, file reads, content search, local docs, workspace indexing, adapters, and safe source links.
- Ollama-backed answers for open-ended chat and model-planned tool use.
- Guarded shell and mutation tools that require confirmation before risky actions.
- A research flow that can gather local or hybrid sources and save reports under `state/research/`.
- A benchmark command that profiles your installed Ollama models and improves local model routing.
- An optional Ollama-compatible wrapper for clients that expect `/api/chat` or `/api/generate`.
- Optional desktop/system integration for user-level launchers, service status, logs, and OS launch paths without changing the default browser UI flow.

## Requirements

- Python 3.11 or newer.
- Git.
- Ollama for model-backed chat, benchmarking, and open-ended answers.
- Node.js if you are editing or validating the static web UI. The installers skip the static JS check when Node is unavailable.

Deterministic local tool routes such as `find file README` can work without Ollama. Normal chat and benchmarking need Ollama running locally.

## 1. Install Ollama First

Install Ollama before installing this project so the setup and doctor checks can see your local model service.

Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

macOS or Windows:

Download and install Ollama from `https://ollama.com/download`, then open a new terminal or PowerShell window.

Pull the default general model used by this project:

```bash
ollama pull qwen3:8b
ollama list
```

If `ollama list` cannot connect, start Ollama and try again:

```bash
ollama serve
```

Leave Ollama running while you use the app. After this project is installed, `tooling-showcase benchmark --list-models` shows what the app can see.

## 2. Install This Project

Linux or macOS:

```bash
git clone https://github.com/Small-ed1/local-llm-tooling-showcase.git
cd local-llm-tooling-showcase
./install.sh
tooling-showcase doctor
```

Windows PowerShell:

```powershell
git clone https://github.com/Small-ed1/local-llm-tooling-showcase.git
cd local-llm-tooling-showcase
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
tooling-showcase doctor
```

`./install.sh` can create `.venv`, install development tools, run tests, run static JavaScript checks, prompt for local model benchmarking when several Ollama models are installed, and optionally install desktop integration.

`.\install-windows.ps1` creates or reuses `.venv`, installs `.[dev]`, runs tests, runs the static JavaScript syntax check when Node is available, runs `tooling-showcase doctor`, and reports whether Ollama model inventory is reachable.

Desktop/system integration is optional. The normal browser UI still works without it.

```bash
./install.sh --with-desktop
./install.sh --no-desktop
./install.sh --desktop-only
./install.sh --repair-desktop
```

Windows PowerShell uses matching switches: `-WithDesktop`, `-NoDesktop`, `-DesktopOnly`, and `-RepairDesktop`.

`--desktop-only` and `--repair-desktop` run only the desktop install/repair action and exit without running the normal setup prompts, tests, or benchmark checks.

Manual setup if you do not want to use the installer:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
tooling-showcase doctor
```

Windows manual activation is `.\.venv\Scripts\Activate.ps1`, and the install command is `python -m pip install -e ".[dev]"`.

## 3. Start The Web UI

```bash
tooling-showcase serve
```

Open:

```text
http://127.0.0.1:8123
```

Try these prompts first:

```text
find file README
read file README.md
search content ToolRuntime
what can this project do?
```

The server binds to `127.0.0.1` by default. Do not bind to `0.0.0.0` unless you understand the safety model and intentionally want LAN access.

## Optional Desktop Integration

Desktop/system integration is official but optional in v1.1.0. It is user-level by default, reversible, and does not silently enable autostart, file actions, hotkeys, tray helpers, or protocol handlers.

Linux support is first-class in v1.1.0:

- Launcher: `~/.local/share/applications/tooling-showcase.desktop`
- User service: `~/.config/systemd/user/tooling-showcase.service`
- Logs: `~/.local/share/tooling-showcase/logs/`

Windows and macOS are recognized safe stubs in v1.1.0 unless noted otherwise by `tooling-showcase desktop status`.

Manage desktop integration:

```bash
tooling-showcase status
tooling-showcase open
tooling-showcase start
tooling-showcase stop
tooling-showcase restart
tooling-showcase logs
tooling-showcase desktop status
tooling-showcase desktop install
tooling-showcase desktop repair
tooling-showcase desktop uninstall
```

## Model Setup Tips

- `qwen3:8b` is the default general model and is the best first model to pull.
- `tooling-showcase models` shows the static routing categories and installed-model guidance.
- `tooling-showcase benchmark --list-models` shows local Ollama inventory without running the full benchmark.
- `tooling-showcase benchmark --limit-tasks 2` is a quick benchmark smoke run.
- `tooling-showcase benchmark` profiles unbenchmarked local models and stores results in `state/model_benchmarks.json`.
- If you only want deterministic tool routes, run a command with `TOOLING_SHOWCASE_OLLAMA_ENABLED=false`.

Example deterministic check without model fallback:

```bash
TOOLING_SHOWCASE_OLLAMA_ENABLED=false tooling-showcase ask "find file README"
```

## Common Commands

```bash
tooling-showcase doctor
tooling-showcase ask "find file README"
tooling-showcase ask "read file README.md"
tooling-showcase ask "search content ToolRuntime"
tooling-showcase journal --limit 5
tooling-showcase adapters
tooling-showcase models
tooling-showcase benchmark --list-models
tooling-showcase status
tooling-showcase desktop status
```

## Data And Privacy

- Browser sessions, settings, prompts, avatars, and UI memories live in browser local storage.
- Backend memories, benchmark profiles, research sessions, event journals, logs, indexes, tasks, and tool stats live under ignored `state/` files.
- Desktop integration logs live under user data paths such as `~/.local/share/tooling-showcase/logs/`, `%LOCALAPPDATA%\tooling-showcase\logs\`, or `~/Library/Logs/tooling-showcase/`.
- Model-created memories are stored locally in `state/memories.json`; do not store secrets there.
- Manual `/api/tool` access is disabled on non-loopback binds unless explicitly enabled with `--enable-remote-tool-api` or `TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API=1`.
- Shell execution is guarded; risky commands and mutation tools require confirmation.

## Known Limits

- This is a local-first runtime, not a sandbox. Local tools can inspect the configured workspace.
- Ollama-backed open-ended answers, benchmarking, and model-profile derivation require a running local Ollama service.
- First model pulls can be large and slow, depending on the model and network.
- The static web UI has no build step; browser/UI edits are validated with `node --check` and smoke tests.
- Benchmark results are local ignored state and are not shipped with the release.
- Windows and macOS desktop integration are v1.1.0 stubs; Linux is the first-class desktop integration platform for this release.

## Troubleshooting

If chat says Ollama is unavailable:

```bash
ollama list
curl http://127.0.0.1:11434/api/tags
tooling-showcase doctor
```

If the web UI does not load:

```bash
tooling-showcase serve --host 127.0.0.1 --port 8123
```

If a tool is rejected, it is usually because the tool is not planner-visible, requires confirmation, or the model asked for an invalid tool name. See `docs/TOOLS.md` for the stable planner tool list.

Useful docs:

- `docs/INSTALL.md` for clean-clone, wheel, and `pipx` install checks.
- `docs/CONFIGURATION.md` for ports, environment variables, and browser storage keys.
- `docs/TOOLS.md` for stable planner tools versus experimental runtime tools.
- `docs/BENCHMARKING.md` for local model benchmark behavior.
- `docs/OLLAMA_WRAPPER.md` for wrapper endpoints and curl smoke tests.
- `docs/desktop-integration.md` for optional desktop integration commands, safety model, logs, and roadmap.
- `docs/TROUBLESHOOTING.md` for Ollama, benchmark, UI, and state issues.
- `SAFETY.md`, `SAFETY_MODEL.md`, and `SECURITY.md` for local execution boundaries.

## Screenshots

Desktop captures below are refreshed from the v1.0 UI. Mobile captures show the same UI in a phone-sized layout.

| Help and setup | Chat thread |
| --- | --- |
| ![Help page](docs/screenshots/desktop/help-page.png) | ![Chat thread](docs/screenshots/desktop/chat-thread.png) |

| Profile settings | Manual tool console |
| --- | --- |
| ![Profile settings](docs/screenshots/desktop/settings-profile.png) | ![Manual tool console](docs/screenshots/desktop/manual-tool-console.png) |

Mobile captures show the responsive chat, help, and settings flow.

<p>
  <img src="docs/screenshots/mobile/chat-mobile.png" alt="Mobile chat" width="260" />
  <img src="docs/screenshots/mobile/settings-mobile.png" alt="Mobile settings" width="260" />
  <img src="docs/screenshots/mobile/help-mobile.png" alt="Mobile help" width="260" />
</p>

## Release Packages

The v1.1 release is shipped as a Python wheel plus source archives.

- The wheel contains the installable `tooling_showcase` package, console entry points, and static UI assets.
- The source distribution and clean source zip include `src/`, tests, docs, screenshots, examples, packaged desktop integration assets, `install.sh`, `install-windows.ps1`, `start-servers.sh`, `scripts/`, and release documentation.
- Ignored local state such as `state/`, `.venv/`, `.ruff_cache/`, `dist/`, `build/`, benchmark outputs, logs, journals, and personal paths are excluded from release archives.

## Ollama-Compatible Wrapper

Start both the showcase UI and the Ollama-compatible wrapper:

```bash
./start-servers.sh
```

Default endpoints:

- showcase web/API: `http://127.0.0.1:8123`
- raw Ollama: `http://127.0.0.1:11434`
- tool-capable Ollama wrapper: `http://127.0.0.1:11436`

Point local clients at the wrapper when you want familiar Ollama API shapes with this project's tool runtime underneath.

## Developer Checks

Run the release gate from the repo root:

```bash
scripts/release-check.sh
```

Focused checks:

```bash
pytest tests/
node --check src/tooling_showcase/static/app-data.js
node --check src/tooling_showcase/static/markdown.js
node --check src/tooling_showcase/static/app.js
python -m ruff check src tests
```

The browser smoke test is `pytest tests/test_browser_smoke.py`. CI installs Playwright Chromium and runs it as a required browser job; local runs skip when Playwright or Chromium is missing.

## Next Steps

After `v1.1.0`, the repo should move from desktop foundation toward safe local-assistant depth:

- Add planner/tool evals that verify tool choice, confirmation boundaries, invalid JSON recovery, and disabled-Ollama fallbacks.
- Keep reducing tool-surface risk by making planner-visible tools explicit, documented, and covered by tests.
- Improve local UX around Ollama setup, benchmark gaps, timeout tuning, research recovery, and one-click diagnostics.
- Harden packaging with repeated wheel, source distribution, `pipx`, Windows installer, and browser smoke checks.
- Avoid adding broad new tools until the planner/tool regression suite covers the current surface.

## Project Layout

```text
src/tooling_showcase/
  router.py          deterministic intent routing
  service.py         chat orchestration, tool loop, logging
  tools.py           local tool runtime and safety gates
  tool_protocol.py   planner-visible tool schemas
  model_routing.py   task-specific model profiles
  benchmarking.py    local Ollama benchmark suite and profile derivation
  research/          research planning, runs, reports, and storage
  desktop/           optional desktop/system integration manager and assets
  server.py          stdlib web UI/API server
  ollama_wrapper.py  Ollama-compatible API facade
  static/            browser UI
tests/               regression tests
examples/assets/     small demo inputs for optional tools
examples/integrations/hyprland/
                     optional Hyprland sidebar integration
```

## Release Status

Current release: `v1.1.0`.

The `v1.1.0` line adds the optional desktop/system integration foundation while preserving the default backend, browser UI, and CLI install path. Linux integration is first-class; Windows and macOS are recognized safe stubs pending fuller native support.

## License

MIT. See `LICENSE`.
