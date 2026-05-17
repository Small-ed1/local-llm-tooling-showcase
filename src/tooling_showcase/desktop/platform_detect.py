from __future__ import annotations

import platform as platform_lib
import sys


def detect_platform(platform_name: str | None = None) -> str:
    raw = (platform_name or sys.platform).lower()
    if raw.startswith("linux"):
        return "linux"
    if raw in {"darwin", "mac", "macos"}:
        return "macos"
    if raw.startswith("win") or raw in {"cygwin", "msys"}:
        return "windows"
    return raw


def platform_info(platform_name: str | None = None) -> dict[str, str]:
    return {
        "platform": detect_platform(platform_name),
        "python_platform": platform_name or sys.platform,
        "system": platform_lib.system(),
        "release": platform_lib.release(),
        "machine": platform_lib.machine(),
        "python": platform_lib.python_version(),
    }
