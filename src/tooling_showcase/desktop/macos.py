from __future__ import annotations

from pathlib import Path
import os

from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.desktop.status import DesktopActionResult, DesktopPaths, DesktopStatus

APP_ID = "tooling-showcase"


def macos_paths(env: dict[str, str] | None = None, home: Path | None = None) -> DesktopPaths:
    env = os.environ if env is None else env
    home_path = Path(home or env.get("HOME") or Path.home()).expanduser()
    logs_dir = home_path / "Library" / "Logs" / APP_ID
    data_dir = home_path / "Library" / "Application Support" / APP_ID
    launch_agent = home_path / "Library" / "LaunchAgents" / "com.small-ed.tooling-showcase.plist"
    return DesktopPaths(
        data_dir=data_dir,
        logs_dir=logs_dir,
        desktop_log=logs_dir / "desktop.log",
        server_log=logs_dir / "server.log",
        pid_file=data_dir / "server.pid",
        launcher=None,
        service=launch_agent,
    )


def status(config: ShowcaseConfig | None = None) -> DesktopStatus:
    paths = macos_paths()
    service_installed = bool(paths.service and paths.service.exists())
    return DesktopStatus(
        supported=True,
        platform="macos",
        installed=service_installed,
        state="stub" if not service_installed else "partial",
        launcher_installed=False,
        service_installed=service_installed,
        service_known=None,
        service_running=False,
        autostart_enabled=False,
        local_url="http://127.0.0.1:8123",
        logs_path=str(paths.logs_dir),
        launcher_path=None,
        service_path=str(paths.service),
        notes=[
            "macOS desktop integration is recognized but not fully implemented in v1.1.0.",
            "Planned macOS support includes a menu bar app, LaunchAgent, Finder Quick Actions, and protocol handler.",
            "Signing and notarization are intentionally out of scope for v1.1.0.",
        ],
        paths=paths.to_dict(),
    )


def install(config: ShowcaseConfig, *, dry_run: bool = False, autostart: bool = False, repair: bool = False) -> DesktopActionResult:
    paths = macos_paths()
    note = "macOS install is a safe v1.1.0 stub; no LaunchAgent is installed automatically."
    plan = [{"action": "no_op_stub", "path": str(paths.service), "requires_sudo": False}]
    return DesktopActionResult(True, "repair" if repair else "install", "macos", dry_run, [], [], [note], plan, status(config).to_dict())


def uninstall(config: ShowcaseConfig, *, dry_run: bool = False) -> DesktopActionResult:
    paths = macos_paths()
    plan = [{"action": "remove_file_if_created_later", "path": str(paths.service), "requires_sudo": False}]
    return DesktopActionResult(True, "uninstall", "macos", dry_run, [], [], ["macOS uninstall is a safe no-op for the v1.1.0 stub."], plan, status(config).to_dict())


def repair(config: ShowcaseConfig, *, dry_run: bool = False, autostart: bool = False) -> DesktopActionResult:
    return install(config, dry_run=dry_run, autostart=autostart, repair=True)
