# Hypr Sidebar

This is a left-side assistant sidebar for Hyprland that lives on a special workspace.

It is designed to:
- open and close with the same Hyprland keybind by toggling a special workspace
- stay locked to the left edge by default while still allowing temporary unlock + repositioning
- remember sessions, geometry, styling, model tuning, and prompt overrides between launches
- inspect workspaces and windows through `hyprctl`
- provide tabs for chat, lite file browsing, local RAG, manual tool calling, desktop control, and settings
- send natural-language requests to the local Python runtime for chat/tool work and to the Hyprland backend for desktop actions

## Requirements

- Hyprland
- `hyprctl`
- AGS (`ags`)
- Python access to this repo (`PYTHONPATH=src`)
- a working local Ollama setup if you want LLM-planned actions

Note: AGS was not installed on this machine when this was scaffolded, so the Python backend is validated but the AGS app itself is provided as a ready-to-run config rather than being executed here.

## Files

- `ags/app.ts`: AGS window and UI
- `ags/style.css`: AGS styling
- `launch.sh`: launcher that sets `PYTHONPATH`
- `hyprland.conf.example`: Hyprland snippet

## Backend

The backend lives in:

- `src/tooling_showcase/hypr_sidebar.py`

It supports:

```bash
PYTHONPATH=src python -m tooling_showcase.hypr_sidebar status
PYTHONPATH=src python -m tooling_showcase.hypr_sidebar act "move the active window to workspace 3"
```

Direct actions are handled with heuristics first. More open-ended requests are planned through the configured Ollama model and executed via `hyprctl dispatch ...`.

## Hypr setup

Copy the contents of `hyprland.conf.example` into your Hyprland config, or adapt the bindings.

The default toggle is:

```text
SUPER + A
```

With AGS v3, the relevant commands are:

```bash
examples/integrations/hyprland/launch.sh
ags request toggle-sidebar -i tooling-showcase-sidebar
ags request toggle-lock -i tooling-showcase-sidebar
ags request opacity-up -i tooling-showcase-sidebar
ags request opacity-down -i tooling-showcase-sidebar
```

## Controls

- Toggle the same keybind to show or hide the special-workspace sidebar
- Unlock the sidebar if you want to drag or resize it, then lock it again to keep it stable
- Click `-` / `+` to change opacity
- Use the tabs for chat, files, RAG, manual tools, desktop control, and settings
- Reorder tabs from the settings page
- Tune chat/planner models, temperature, repeat penalty, `top_p`, and prompt overrides from the settings page
- The sidebar polls Hyprland client geometry and persists the last seen position and size
- Settings are stored in `~/.config/tooling-showcase-hypr-sidebar/settings.json`
- Sessions are stored in `~/.config/tooling-showcase-hypr-sidebar/sessions.json`

## Persistence

The AGS window stores its layout and tuning state in:

```text
~/.config/tooling-showcase-hypr-sidebar/settings.json
~/.config/tooling-showcase-hypr-sidebar/sessions.json
```

Closing and reopening the sidebar restores sessions, tab order, styling, prompts, model settings, and the last known geometry.
