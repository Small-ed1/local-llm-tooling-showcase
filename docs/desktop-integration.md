# Desktop And System Integration

The v1.1.0 desktop/system integration foundation is optional, official, reversible, and safe. The default install remains backend, browser UI, and CLI.

Packaged desktop reference assets live under `src/tooling_showcase/desktop/assets/` in this checkout.

## v1.1.0 Implemented

- Optional installer flags for desktop integration.
- CLI status/open/start/stop/restart/log commands.
- CLI desktop status/install/repair/uninstall/logs/open commands.
- Linux user-level `.desktop` launcher.
- Linux user-level `systemd --user` service file.
- Read-only `/api/desktop/status` and related system status endpoints.
- Settings panel status display.
- User-level logs under project-specific data directories.
- Tests for path safety, status shape, CLI status, and endpoint JSON.

## Safety Model

- User-level install only by default.
- No `sudo` or admin writes.
- Install and repair print or record changed paths.
- Uninstall removes only known project-owned launcher/service files.
- No web endpoint installs, repairs, removes, or starts OS integration in v1.1.0.
- Autostart is not enabled unless the user explicitly asks for it.
- File actions, hotkeys, protocol handlers, and tray/menu-bar helpers are not silently installed.

## Commands

Inspect everything:

```bash
tooling-showcase status
tooling-showcase desktop status
```

Install Linux desktop integration:

```bash
tooling-showcase desktop install
```

Repair or remove:

```bash
tooling-showcase desktop repair
tooling-showcase desktop uninstall
```

Open or manage the backend:

```bash
tooling-showcase open
tooling-showcase start
tooling-showcase stop
tooling-showcase restart
tooling-showcase logs
```

## Log Locations

Linux:

```text
~/.local/share/tooling-showcase/logs/
```

Windows:

```text
%LOCALAPPDATA%\tooling-showcase\logs\
```

macOS:

```text
~/Library/Logs/tooling-showcase/
```

## Platform Status

Linux is first-class in v1.1.0. Non-systemd Linux is handled gracefully: launcher files can be installed, while service checks report notes instead of failing.

Windows and macOS are recognized stubs in v1.1.0. They return clear status and no-op safely for install/repair/uninstall until platform-specific implementations are ready.

## Roadmap

v1.2.0 planned features:

- Tray/menu-bar app.
- Quick ask window.
- Clipboard ask.
- File/folder actions.
- Workspace picker.
- Native notifications.
- Settings install/repair/remove controls if they can be made safely localhost-only and confirmation-gated.

v1.3.0 planned features:

- Screenshot ask.
- Protocol handler.
- Global hotkeys.
- Packaged desktop shell.
- Stronger Windows/macOS support.
- Repair wizard.
- Model manager UI.

v2.0.0 should only happen if desktop becomes the primary default UI or major breaking architecture/config changes land.
