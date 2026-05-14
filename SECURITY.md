# Security Policy

This project is a local-first tooling showcase. Treat it as code that can inspect and operate on your workspace. Operational safety notes live in `SAFETY.md`.

## Reporting

Please report security issues privately through GitHub's vulnerability reporting flow, or open a minimal issue that avoids publishing exploit details.

## Local Safety Notes

- Review tool schemas and shell-safety rules before running against sensitive workspaces.
- Keep secrets out of prompts, browser-local settings, example files, and the event journal.
- The shell tool parses common command shapes to block known destructive command/argument patterns and require confirmation for risky commands, but it is not a complete sandbox.
- Default web and wrapper hosts are loopback-only; pass `--host 0.0.0.0` only for intentional LAN exposure.
- `/api/tool` is the direct manual tool runner. It is enabled on loopback binds and disabled by default on non-loopback binds unless `--enable-remote-tool-api` or `TOOLING_SHOWCASE_ENABLE_REMOTE_TOOL_API=1` is set for a trusted network.
