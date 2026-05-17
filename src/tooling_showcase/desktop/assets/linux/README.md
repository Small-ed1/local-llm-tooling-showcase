# Linux Desktop Integration

Linux is the first-class desktop/system integration target for v1.1.0.

Implemented user-level files:

- Launcher: `~/.local/share/applications/tooling-showcase.desktop`
- User service: `~/.config/systemd/user/tooling-showcase.service`
- Logs: `~/.local/share/tooling-showcase/logs/`

Install:

```bash
tooling-showcase desktop install
```

Inspect or repair:

```bash
tooling-showcase desktop status
tooling-showcase desktop repair
tooling-showcase desktop logs
```

Remove:

```bash
tooling-showcase desktop uninstall
```

Safety behavior:

- Installs only user-level files by default.
- Does not require `sudo`.
- Does not enable autostart unless `tooling-showcase desktop install --autostart` is used.
- Does not install tray apps, file-manager actions, hotkeys, or protocol handlers in v1.1.0.
- Non-systemd Linux is supported for launcher installation and reports service checks as notes instead of failing.

The Python installer renders equivalent files with the active Python/module path so editable installs, virtual environments, and wheel installs can work reliably.
