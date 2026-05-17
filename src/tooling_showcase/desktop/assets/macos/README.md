# macOS Desktop Integration

macOS is recognized in v1.1.0, but desktop integration is a safe stub.

Current behavior:

- `tooling-showcase desktop status` reports macOS as a known platform.
- `tooling-showcase desktop install`, `repair`, and `uninstall` are safe no-ops.
- No LaunchAgent is installed automatically.
- No app bundle, signing, notarization, Finder Quick Actions, or protocol handlers are attempted.

Planned support:

- Menu bar app later.
- LaunchAgent after explicit opt-in.
- Finder Quick Actions later.
- Protocol handler later.

Use the normal web UI and CLI on macOS:

```bash
tooling-showcase serve
tooling-showcase open
```
