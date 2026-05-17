from __future__ import annotations

from tooling_showcase.desktop.manager import (
    backend_status,
    desktop_status,
    install_desktop,
    open_local_ui,
    recent_logs,
    repair_desktop,
    restart_backend,
    start_backend,
    stop_backend,
    system_status,
    uninstall_desktop,
)
from tooling_showcase.desktop.status import DesktopActionResult, DesktopStatus

__all__ = [
    "DesktopActionResult",
    "DesktopStatus",
    "backend_status",
    "desktop_status",
    "install_desktop",
    "open_local_ui",
    "recent_logs",
    "repair_desktop",
    "restart_backend",
    "start_backend",
    "stop_backend",
    "system_status",
    "uninstall_desktop",
]
