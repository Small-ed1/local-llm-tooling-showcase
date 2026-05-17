from __future__ import annotations

from pathlib import Path
import os

from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.desktop.status import DesktopActionResult, DesktopPaths, DesktopStatus

APP_ID = "tooling-showcase"


def windows_paths(env: dict[str, str] | None = None, home: Path | None = None) -> DesktopPaths:
    env = os.environ if env is None else env
    home_path = Path(home or env.get("USERPROFILE") or Path.home()).expanduser()
    data_dir = Path(env.get("LOCALAPPDATA") or home_path / "AppData" / "Local") / APP_ID
    logs_dir = data_dir / "logs"
    start_menu = Path(env.get("APPDATA") or home_path / "AppData" / "Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return DesktopPaths(
        data_dir=data_dir,
        logs_dir=logs_dir,
        desktop_log=logs_dir / "desktop.log",
        server_log=logs_dir / "server.log",
        pid_file=data_dir / "server.pid",
        launcher=start_menu / "Local LLM Tooling Showcase.url",
        service=None,
    )


def status(config: ShowcaseConfig | None = None) -> DesktopStatus:
    paths = windows_paths()
    launcher_installed = bool(paths.launcher and paths.launcher.exists())
    return DesktopStatus(
        supported=True,
        platform="windows",
        installed=launcher_installed,
        state="stub" if not launcher_installed else "partial",
        launcher_installed=launcher_installed,
        service_installed=False,
        service_known=None,
        service_running=False,
        autostart_enabled=False,
        local_url="http://127.0.0.1:8123",
        logs_path=str(paths.logs_dir),
        launcher_path=str(paths.launcher),
        service_path=None,
        notes=[
            "Windows desktop integration is recognized but not fully implemented in v1.1.0.",
            "Planned Windows support includes a Start Menu shortcut, optional startup task, Explorer actions, and protocol handler.",
            "No registry keys are created by the v1.1.0 stub.",
        ],
        paths=paths.to_dict(),
    )


def install(config: ShowcaseConfig, *, dry_run: bool = False, autostart: bool = False, repair: bool = False) -> DesktopActionResult:
    paths = windows_paths()
    note = "Windows install is a safe v1.1.0 stub; no shortcuts, startup tasks, or registry keys are modified."
    plan = [{"action": "no_op_stub", "path": str(paths.launcher), "requires_sudo": False}]
    return DesktopActionResult(True, "repair" if repair else "install", "windows", dry_run, [], [], [note], plan, status(config).to_dict())


def uninstall(config: ShowcaseConfig, *, dry_run: bool = False) -> DesktopActionResult:
    paths = windows_paths()
    plan = [{"action": "remove_file_if_created_later", "path": str(paths.launcher), "requires_sudo": False}]
    return DesktopActionResult(True, "uninstall", "windows", dry_run, [], [], ["Windows uninstall is a safe no-op for the v1.1.0 stub."], plan, status(config).to_dict())


def repair(config: ShowcaseConfig, *, dry_run: bool = False, autostart: bool = False) -> DesktopActionResult:
    return install(config, dry_run=dry_run, autostart=autostart, repair=True)
