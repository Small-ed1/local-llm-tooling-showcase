from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import shutil
import subprocess
import sys

from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.desktop.status import DesktopActionResult, DesktopPaths, DesktopStatus

SERVICE_NAME = "tooling-showcase.service"
APP_ID = "tooling-showcase"


def linux_paths(env: dict[str, str] | None = None, home: Path | None = None) -> DesktopPaths:
    env = os.environ if env is None else env
    home_path = Path(home or env.get("HOME") or Path.home()).expanduser()
    data_home = Path(env.get("XDG_DATA_HOME") or home_path / ".local" / "share").expanduser()
    config_home = Path(env.get("XDG_CONFIG_HOME") or home_path / ".config").expanduser()
    data_dir = data_home / APP_ID
    logs_dir = data_dir / "logs"
    return DesktopPaths(
        data_dir=data_dir,
        logs_dir=logs_dir,
        desktop_log=logs_dir / "desktop.log",
        server_log=logs_dir / "server.log",
        pid_file=data_dir / "server.pid",
        launcher=data_home / "applications" / f"{APP_ID}.desktop",
        service=config_home / "systemd" / "user" / SERVICE_NAME,
    )


def install_plan(config: ShowcaseConfig, *, autostart: bool = False) -> list[dict[str, str | bool | None]]:
    paths = linux_paths()
    plan: list[dict[str, str | bool | None]] = [
        {"action": "create_directory", "path": str(paths.logs_dir), "requires_sudo": False},
        {"action": "create_directory", "path": str(paths.launcher.parent if paths.launcher else ""), "requires_sudo": False},
        {"action": "create_directory", "path": str(paths.service.parent if paths.service else ""), "requires_sudo": False},
        {"action": "write_file", "path": str(paths.launcher), "requires_sudo": False},
        {"action": "write_file", "path": str(paths.service), "requires_sudo": False},
        {"action": "systemd_user_daemon_reload", "path": None, "requires_sudo": False},
    ]
    if autostart:
        plan.append({"action": "systemd_user_enable", "path": SERVICE_NAME, "requires_sudo": False})
    return plan


def uninstall_plan(*, service_running: bool = False) -> list[dict[str, str | bool | None]]:
    paths = linux_paths()
    plan: list[dict[str, str | bool | None]] = []
    if service_running:
        plan.append({"action": "systemd_user_stop", "path": SERVICE_NAME, "requires_sudo": False})
    plan.extend([
        {"action": "systemd_user_disable", "path": SERVICE_NAME, "requires_sudo": False},
        {"action": "remove_file", "path": str(paths.launcher), "requires_sudo": False},
        {"action": "remove_file", "path": str(paths.service), "requires_sudo": False},
        {"action": "systemd_user_daemon_reload", "path": None, "requires_sudo": False},
    ])
    return plan


def status(config: ShowcaseConfig | None = None) -> DesktopStatus:
    paths = linux_paths()
    launcher_installed = bool(paths.launcher and paths.launcher.exists())
    service_installed = bool(paths.service and paths.service.exists())
    notes: list[str] = []

    service_known: bool | None = None
    service_running = False
    autostart_enabled = False
    if _systemctl_path():
        load_state = _systemctl_value(["show", SERVICE_NAME, "--property=LoadState", "--value"], notes)
        if load_state:
            service_known = load_state == "loaded"
        service_running = _systemctl_ok(["is-active", "--quiet", SERVICE_NAME], notes, quiet_expected=True)
        autostart_enabled = _systemctl_ok(["is-enabled", "--quiet", SERVICE_NAME], notes, quiet_expected=True)
    else:
        notes.append("systemctl is unavailable; service state checks are skipped on this Linux environment.")

    installed = launcher_installed and service_installed
    if installed:
        state = "installed"
    elif launcher_installed or service_installed:
        state = "broken"
        notes.append("Desktop integration is partially installed. Run: tooling-showcase desktop repair")
    else:
        state = "not_installed"

    if installed and not autostart_enabled:
        notes.append("Autostart is disabled. This is the default unless desktop install is run with --autostart.")
    notes.append("Tray, file actions, and protocol handlers are planned add-ons and are not installed in v1.1.0.")

    return DesktopStatus(
        supported=True,
        platform="linux",
        installed=installed,
        state=state,
        launcher_installed=launcher_installed,
        service_installed=service_installed,
        service_known=service_known,
        service_running=service_running,
        autostart_enabled=autostart_enabled,
        local_url="http://127.0.0.1:8123",
        logs_path=str(paths.logs_dir),
        launcher_path=str(paths.launcher),
        service_path=str(paths.service),
        notes=_dedupe_notes(notes),
        paths=paths.to_dict(),
    )


def install(config: ShowcaseConfig, *, dry_run: bool = False, autostart: bool = False, repair: bool = False) -> DesktopActionResult:
    paths = linux_paths()
    plan = install_plan(config, autostart=autostart)
    notes = ["Linux install is user-level only and does not require sudo."]
    changed: list[str] = []
    skipped: list[str] = []

    if dry_run:
        return DesktopActionResult(True, "repair" if repair else "install", "linux", True, [], [], notes, plan, status(config).to_dict())

    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    for directory in [paths.launcher.parent if paths.launcher else None, paths.service.parent if paths.service else None]:
        if directory:
            directory.mkdir(parents=True, exist_ok=True)
            changed.append(str(directory))

    launcher_text = _desktop_file_text(config)
    service_text = _service_file_text(config, paths)
    if paths.launcher and _write_if_changed(paths.launcher, launcher_text):
        changed.append(str(paths.launcher))
    else:
        skipped.append(str(paths.launcher))
    if paths.service and _write_if_changed(paths.service, service_text):
        changed.append(str(paths.service))
    else:
        skipped.append(str(paths.service))

    _log(paths, f"{('repair' if repair else 'install')} wrote launcher={paths.launcher} service={paths.service}")
    if _systemctl_path():
        _systemctl_note(["daemon-reload"], notes)
        if autostart:
            if _systemctl_ok(["enable", SERVICE_NAME], notes):
                changed.append(f"systemd-user:{SERVICE_NAME}:enabled")
        else:
            notes.append("Service was installed but not enabled for autostart.")
    else:
        notes.append("systemctl is unavailable; service file was installed but daemon-reload was skipped.")

    result_status = status(config).to_dict()
    return DesktopActionResult(True, "repair" if repair else "install", "linux", False, changed, skipped, _dedupe_notes(notes), plan, result_status)


def uninstall(config: ShowcaseConfig, *, dry_run: bool = False) -> DesktopActionResult:
    paths = linux_paths()
    status_before = status(config)
    plan = uninstall_plan(service_running=status_before.service_running)
    notes = ["Uninstall removes only project-owned launcher and user service files. Logs are kept for diagnostics."]
    changed: list[str] = []
    skipped: list[str] = []

    if dry_run:
        return DesktopActionResult(True, "uninstall", "linux", True, [], [], notes, plan, status_before.to_dict())

    if _systemctl_path():
        if status_before.service_running:
            if _systemctl_ok(["stop", SERVICE_NAME], notes):
                changed.append(f"systemd-user:{SERVICE_NAME}:stopped")
            else:
                notes.append("Service is active and could not be stopped; leaving integration files in place so uninstall can be retried safely.")
                return DesktopActionResult(False, "uninstall", "linux", False, changed, skipped, _dedupe_notes(notes), plan, status(config).to_dict())
        _systemctl_ok(["disable", SERVICE_NAME], notes, quiet_expected=True)
    else:
        notes.append("systemctl is unavailable; service stop/disable checks were skipped.")

    for path in [paths.launcher, paths.service]:
        if path and path.exists():
            path.unlink()
            changed.append(str(path))
        elif path:
            skipped.append(str(path))

    if _systemctl_path():
        _systemctl_note(["daemon-reload"], notes)
    if paths.logs_dir.exists():
        _log(paths, f"uninstall removed paths={changed}")
    return DesktopActionResult(True, "uninstall", "linux", False, changed, skipped, _dedupe_notes(notes), plan, status(config).to_dict())


def repair(config: ShowcaseConfig, *, dry_run: bool = False, autostart: bool = False) -> DesktopActionResult:
    return install(config, dry_run=dry_run, autostart=autostart, repair=True)


def start_service(notes: list[str] | None = None) -> bool:
    return _systemctl_ok(["start", SERVICE_NAME], notes if notes is not None else [])


def stop_service(notes: list[str] | None = None) -> bool:
    return _systemctl_ok(["stop", SERVICE_NAME], notes if notes is not None else [])


def systemd_available() -> bool:
    return bool(_systemctl_path())


def _desktop_file_text(config: ShowcaseConfig) -> str:
    command = _python_module_command("open")
    return f"""[Desktop Entry]
Type=Application
Name=Local LLM Tooling Showcase
Comment=Open the local Local LLM Tooling Showcase web UI
Exec={command}
Terminal=false
Categories=Development;Utility;
StartupNotify=true
X-ToolingShowcase=1
"""


def _service_file_text(config: ShowcaseConfig, paths: DesktopPaths) -> str:
    serve_command = _python_module_command("serve --host 127.0.0.1 --port 8123")
    return f"""[Unit]
Description=Local LLM Tooling Showcase web UI
Documentation=https://github.com/Small-ed1/local-llm-tooling-showcase
After=network.target

[Service]
Type=simple
WorkingDirectory={config.project_root}
ExecStart={serve_command}
Restart=on-failure
RestartSec=2
StandardOutput=append:{paths.server_log}
StandardError=append:{paths.server_log}

[Install]
WantedBy=default.target
"""


def _python_module_command(cli_args: str) -> str:
    executable = sys.executable.replace("%", "%%")
    return f"{executable} -m tooling_showcase.cli {cli_args}"


def _write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def _systemctl_path() -> str | None:
    return shutil.which("systemctl")


def _systemctl_command(args: list[str]) -> list[str]:
    return ["systemctl", "--user", *args]


def _systemctl_value(args: list[str], notes: list[str]) -> str | None:
    try:
        result = subprocess.run(_systemctl_command(args), capture_output=True, text=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        notes.append(f"systemctl --user check skipped: {exc}")
        return None
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        if detail:
            notes.append(f"systemctl --user unavailable for {SERVICE_NAME}: {detail}")
        return None
    return result.stdout.strip()


def _systemctl_ok(args: list[str], notes: list[str], *, quiet_expected: bool = False) -> bool:
    try:
        result = subprocess.run(_systemctl_command(args), capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        notes.append(f"systemctl --user {' '.join(args)} skipped: {exc}")
        return False
    if result.returncode == 0:
        return True
    if not quiet_expected:
        detail = (result.stderr or result.stdout).strip()
        if detail:
            notes.append(f"systemctl --user {' '.join(args)} failed: {detail}")
    return False


def _systemctl_note(args: list[str], notes: list[str]) -> None:
    if _systemctl_ok(args, notes):
        notes.append(f"Ran systemctl --user {' '.join(args)}.")


def _log(paths: DesktopPaths, message: str) -> None:
    try:
        paths.logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat()
        with paths.desktop_log.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {message}\n")
    except OSError:
        return


def _dedupe_notes(notes: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for note in notes:
        if note and note not in seen:
            out.append(note)
            seen.add(note)
    return out
