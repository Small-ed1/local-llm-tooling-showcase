# Windows Desktop Integration

Windows is recognized in v1.1.0, but desktop integration is a safe stub.

Current behavior:

- `tooling-showcase desktop status` reports Windows as a known platform.
- `tooling-showcase desktop install`, `repair`, and `uninstall` are safe no-ops.
- No registry keys are created.
- No startup tasks are created.
- No Explorer right-click actions or protocol handlers are registered.

Planned support:

- Start Menu shortcut.
- Optional startup task, only after explicit user opt-in.
- Explorer right-click file/folder actions later.
- Protocol handler later.

Use the normal web UI and CLI on Windows:

```powershell
tooling-showcase serve
tooling-showcase open
```
