from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class DesktopPaths:
    data_dir: Path
    logs_dir: Path
    desktop_log: Path
    server_log: Path
    pid_file: Path
    launcher: Path | None = None
    service: Path | None = None
    autostart: Path | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {key: str(value) if value is not None else None for key, value in asdict(self).items()}


@dataclass(slots=True)
class DesktopStatus:
    supported: bool
    platform: str
    installed: bool = False
    state: str = "not_installed"
    launcher_installed: bool = False
    service_installed: bool = False
    service_known: bool | None = None
    service_running: bool = False
    autostart_enabled: bool = False
    tray_installed: bool = False
    file_actions_installed: bool = False
    protocol_handler_installed: bool = False
    local_url: str = "http://127.0.0.1:8123"
    logs_path: str = ""
    launcher_path: str | None = None
    service_path: str | None = None
    notes: list[str] = field(default_factory=list)
    paths: dict[str, str | None] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class DesktopActionResult:
    ok: bool
    action: str
    platform: str
    dry_run: bool = False
    changed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    plan: list[dict[str, str | bool | None]] = field(default_factory=list)
    status: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def unsupported_status(platform_name: str) -> DesktopStatus:
    return DesktopStatus(
        supported=False,
        platform=platform_name,
        state="unsupported",
        notes=[
            f"Desktop integration is not implemented for platform '{platform_name}'.",
            "No OS-level files are installed or modified on unsupported platforms.",
        ],
    )
