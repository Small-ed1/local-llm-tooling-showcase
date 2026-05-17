from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import os
import signal
import subprocess
import sys
import time
import webbrowser

from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.desktop import linux, macos, windows
from tooling_showcase.desktop.platform_detect import detect_platform, platform_info
from tooling_showcase.desktop.status import DesktopActionResult, DesktopPaths, DesktopStatus, unsupported_status

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8123


def desktop_status(config: ShowcaseConfig | None = None, *, platform_name: str | None = None) -> DesktopStatus:
    platform_key = detect_platform(platform_name)
    if platform_key == "linux":
        return linux.status(config)
    if platform_key == "windows":
        return windows.status(config)
    if platform_key == "macos":
        return macos.status(config)
    return unsupported_status(platform_key)


def install_desktop(
    config: ShowcaseConfig,
    *,
    dry_run: bool = False,
    autostart: bool = False,
    platform_name: str | None = None,
) -> DesktopActionResult:
    platform_key = detect_platform(platform_name)
    if platform_key == "linux":
        return linux.install(config, dry_run=dry_run, autostart=autostart)
    if platform_key == "windows":
        return windows.install(config, dry_run=dry_run, autostart=autostart)
    if platform_key == "macos":
        return macos.install(config, dry_run=dry_run, autostart=autostart)
    return _unsupported_action("install", platform_key, dry_run=dry_run)


def uninstall_desktop(config: ShowcaseConfig, *, dry_run: bool = False, platform_name: str | None = None) -> DesktopActionResult:
    platform_key = detect_platform(platform_name)
    if platform_key == "linux":
        return linux.uninstall(config, dry_run=dry_run)
    if platform_key == "windows":
        return windows.uninstall(config, dry_run=dry_run)
    if platform_key == "macos":
        return macos.uninstall(config, dry_run=dry_run)
    return _unsupported_action("uninstall", platform_key, dry_run=dry_run)


def repair_desktop(
    config: ShowcaseConfig,
    *,
    dry_run: bool = False,
    autostart: bool = False,
    platform_name: str | None = None,
) -> DesktopActionResult:
    platform_key = detect_platform(platform_name)
    if platform_key == "linux":
        return linux.repair(config, dry_run=dry_run, autostart=autostart)
    if platform_key == "windows":
        return windows.repair(config, dry_run=dry_run, autostart=autostart)
    if platform_key == "macos":
        return macos.repair(config, dry_run=dry_run, autostart=autostart)
    return _unsupported_action("repair", platform_key, dry_run=dry_run)


def backend_status(config: ShowcaseConfig, *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 0.5) -> dict:
    url = local_url(host=host, port=port)
    health_url = f"{url}/api/system/health"
    try:
        request = Request(health_url, method="GET")
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"running": True, "ok": True, "url": url, "health_url": health_url, "status": response.status, "data": payload}
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"running": False, "ok": False, "url": url, "health_url": health_url, "error": str(exc)}


def ollama_status(config: ShowcaseConfig, *, timeout: float = 1.5) -> dict:
    tags_url = _ollama_tags_url(config.ollama.endpoint)
    if not config.ollama.enabled:
        return {"ok": False, "enabled": False, "reachable": False, "endpoint": tags_url, "state": "disabled", "error": "Ollama is disabled."}
    try:
        request = Request(tags_url, method="GET")
        with urlopen(request, timeout=min(max(timeout, 0.1), max(0.1, float(config.ollama.timeout_seconds)))) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = data.get("models", []) if isinstance(data, dict) else []
        return {"ok": True, "enabled": True, "reachable": True, "endpoint": tags_url, "state": "online", "model_count": len(models)}
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "enabled": True, "reachable": False, "endpoint": tags_url, "state": "unreachable", "error": str(exc)}


def system_status(config: ShowcaseConfig, *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    desktop = desktop_status(config)
    paths = _runtime_paths(desktop.platform)
    return {
        "ok": True,
        "backend": backend_status(config, host=host, port=port),
        "configured_port": port,
        "local_url": local_url(host=host, port=port),
        "ollama": ollama_status(config),
        "desktop": desktop.to_dict(),
        "service": {
            "installed": desktop.service_installed,
            "known": desktop.service_known,
            "running": desktop.service_running,
            "autostart_enabled": desktop.autostart_enabled,
            "path": desktop.service_path,
        },
        "launcher": {"installed": desktop.launcher_installed, "path": desktop.launcher_path},
        "platform": platform_info(),
        "logs": _log_locations(paths),
    }


def start_backend(config: ShowcaseConfig, *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> DesktopActionResult:
    platform_key = detect_platform()
    notes: list[str] = []
    current = backend_status(config, host=host, port=port)
    if current["running"]:
        return DesktopActionResult(True, "start", platform_key, notes=[f"Backend is already running at {current['url']}"], status=current)

    desktop = desktop_status(config)
    if platform_key == "linux" and desktop.service_installed and host == DEFAULT_HOST and port == DEFAULT_PORT and linux.systemd_available():
        if linux.start_service(notes):
            _wait_for_backend(config, host=host, port=port)
            return DesktopActionResult(True, "start", platform_key, changed=[f"systemd-user:{linux.SERVICE_NAME}:started"], notes=notes, status=backend_status(config, host=host, port=port))

    paths = _runtime_paths(platform_key)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "tooling_showcase.cli", "serve", "--host", host, "--port", str(port)]
    log_handle = paths.server_log.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=str(config.project_root),
        env=os.environ.copy(),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log_handle.close()
    paths.pid_file.write_text(str(process.pid), encoding="utf-8")
    notes.append(f"Started detached backend process {process.pid}; logs: {paths.server_log}")
    _wait_for_backend(config, host=host, port=port)
    status = backend_status(config, host=host, port=port)
    if not status["running"]:
        notes.append("Backend process was launched but did not answer the health check before the timeout.")
    return DesktopActionResult(bool(status["running"]), "start", platform_key, changed=[str(paths.pid_file), str(paths.server_log)], notes=notes, status=status)


def stop_backend(config: ShowcaseConfig, *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> DesktopActionResult:
    platform_key = detect_platform()
    notes: list[str] = []
    desktop = desktop_status(config)
    if platform_key == "linux" and desktop.service_running and linux.systemd_available():
        if linux.stop_service(notes):
            return DesktopActionResult(True, "stop", platform_key, changed=[f"systemd-user:{linux.SERVICE_NAME}:stopped"], notes=notes, status=backend_status(config, host=host, port=port))

    paths = _runtime_paths(platform_key)
    pid = _read_pid(paths.pid_file)
    if pid is None:
        return DesktopActionResult(True, "stop", platform_key, skipped=[str(paths.pid_file)], notes=["No managed backend PID file was found."], status=backend_status(config, host=host, port=port))

    try:
        os.kill(pid, signal.SIGTERM)
        notes.append(f"Sent SIGTERM to backend process {pid}.")
    except ProcessLookupError:
        notes.append(f"Backend process {pid} was not running.")
    except OSError as exc:
        return DesktopActionResult(False, "stop", platform_key, notes=[f"Failed to stop backend process {pid}: {exc}"], status=backend_status(config, host=host, port=port))
    try:
        paths.pid_file.unlink()
    except FileNotFoundError:
        pass
    return DesktopActionResult(True, "stop", platform_key, changed=[str(paths.pid_file)], notes=notes, status=backend_status(config, host=host, port=port))


def restart_backend(config: ShowcaseConfig, *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> DesktopActionResult:
    stopped = stop_backend(config, host=host, port=port)
    time.sleep(0.2)
    started = start_backend(config, host=host, port=port)
    return DesktopActionResult(
        stopped.ok and started.ok,
        "restart",
        detect_platform(),
        changed=[*stopped.changed, *started.changed],
        skipped=[*stopped.skipped, *started.skipped],
        notes=[*stopped.notes, *started.notes],
        status=started.status,
    )


def open_local_ui(config: ShowcaseConfig, *, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, start_if_needed: bool = True) -> DesktopActionResult:
    platform_key = detect_platform()
    current = backend_status(config, host=host, port=port)
    notes: list[str] = []
    changed: list[str] = []
    if not current["running"] and start_if_needed:
        started = start_backend(config, host=host, port=port)
        notes.extend(started.notes)
        changed.extend(started.changed)
        current = backend_status(config, host=host, port=port)
    url = local_url(host=host, port=port)
    opened = webbrowser.open(url)
    notes.append(f"Opened {url} in the system browser." if opened else f"Could not open browser automatically. Open {url} manually.")
    return DesktopActionResult(bool(opened or current["running"]), "open", platform_key, changed=changed, notes=notes, status=current)


def recent_logs(config: ShowcaseConfig, *, lines: int = 40, platform_name: str | None = None) -> dict:
    platform_key = detect_platform(platform_name)
    paths = _runtime_paths(platform_key)
    files = {
        "backend": paths.server_log,
        "desktop": paths.desktop_log,
    }
    entries = {}
    for name, path in files.items():
        entries[name] = {"path": str(path), "exists": path.exists(), "lines": _last_lines(path, lines) if path.exists() else []}
    return {"ok": True, "platform": platform_key, "logs_path": str(paths.logs_dir), "logs": entries}


def local_url(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    return f"http://{host}:{port}"


def _runtime_paths(platform_key: str) -> DesktopPaths:
    if platform_key == "linux":
        return linux.linux_paths()
    if platform_key == "windows":
        return windows.windows_paths()
    if platform_key == "macos":
        return macos.macos_paths()
    home = Path.home()
    data_dir = home / ".local" / "share" / "tooling-showcase"
    logs_dir = data_dir / "logs"
    return DesktopPaths(data_dir, logs_dir, logs_dir / "desktop.log", logs_dir / "server.log", data_dir / "server.pid")


def _log_locations(paths: DesktopPaths) -> dict[str, str]:
    return {"logs_dir": str(paths.logs_dir), "backend": str(paths.server_log), "desktop": str(paths.desktop_log), "pid_file": str(paths.pid_file)}


def _last_lines(path: Path, lines: int) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return content[-max(1, lines):]


def _read_pid(path: Path) -> int | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
        return int(text)
    except (OSError, ValueError):
        return None


def _wait_for_backend(config: ShowcaseConfig, *, host: str, port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if backend_status(config, host=host, port=port, timeout=0.2)["running"]:
            return
        time.sleep(0.1)


def _ollama_tags_url(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if not parsed.scheme or not parsed.netloc:
        return "http://127.0.0.1:11434/api/tags"
    return f"{parsed.scheme}://{parsed.netloc}/api/tags"


def _unsupported_action(action: str, platform_key: str, *, dry_run: bool) -> DesktopActionResult:
    status = unsupported_status(platform_key)
    return DesktopActionResult(False, action, platform_key, dry_run=dry_run, notes=status.notes, status=status.to_dict())
