import json
import sys
from pathlib import Path

from tooling_showcase.cli import main
from tooling_showcase.config import OllamaConfig, ShellPolicy, ShowcaseConfig
from tooling_showcase.desktop import desktop_status, install_desktop
import tooling_showcase.desktop.linux as linux_module
from tooling_showcase.desktop.linux import install_plan, linux_paths, uninstall_plan
from tooling_showcase.desktop.platform_detect import detect_platform


def test_platform_detection_recognizes_supported_names():
    assert detect_platform("linux") == "linux"
    assert detect_platform("linux2") == "linux"
    assert detect_platform("darwin") == "macos"
    assert detect_platform("win32") == "windows"
    assert detect_platform("freebsd") == "freebsd"


def test_unsupported_platform_returns_clean_status(tmp_path):
    status = desktop_status(_config(tmp_path), platform_name="freebsd").to_dict()

    assert status["supported"] is False
    assert status["platform"] == "freebsd"
    assert status["installed"] is False
    assert status["launcher_installed"] is False
    assert status["service_installed"] is False
    assert status["tray_installed"] is False
    assert status["file_actions_installed"] is False
    assert status["protocol_handler_installed"] is False
    assert status["notes"]


def test_linux_install_paths_are_user_level(tmp_path):
    env = {
        "HOME": str(tmp_path / "home"),
        "XDG_DATA_HOME": str(tmp_path / "home" / ".local" / "share"),
        "XDG_CONFIG_HOME": str(tmp_path / "home" / ".config"),
    }
    paths = linux_paths(env=env)

    assert paths.launcher == Path(env["XDG_DATA_HOME"]) / "applications" / "tooling-showcase.desktop"
    assert paths.service == Path(env["XDG_CONFIG_HOME"]) / "systemd" / "user" / "tooling-showcase.service"
    assert str(paths.logs_dir).startswith(str(Path(env["XDG_DATA_HOME"])))
    assert "/etc/" not in str(paths.launcher)
    assert "/etc/" not in str(paths.service)


def test_linux_install_plan_does_not_require_sudo(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    plan = install_plan(_config(tmp_path))

    assert plan
    assert all(item["requires_sudo"] is False for item in plan)
    assert "sudo" not in " ".join(str(item.get("action", "")) for item in plan).lower()


def test_default_linux_install_plan_does_not_enable_autostart(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    plan = install_plan(_config(tmp_path))

    assert "systemd_user_daemon_reload" in _plan_actions(plan)
    assert "systemd_user_enable" not in _plan_actions(plan)


def test_autostart_linux_install_plan_enables_user_service(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    plan = install_plan(_config(tmp_path), autostart=True)

    assert "systemd_user_enable" in _plan_actions(plan)


def test_uninstall_plan_only_targets_project_owned_paths(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    plan = uninstall_plan()
    paths = linux_paths()
    remove_paths = {item["path"] for item in plan if item["action"] == "remove_file"}

    assert remove_paths == {str(paths.launcher), str(paths.service)}
    assert all("tooling-showcase" in path for path in remove_paths)


def test_uninstall_plan_stops_running_user_service(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    plan = uninstall_plan(service_running=True)

    assert plan[0]["action"] == "systemd_user_stop"
    assert plan[0]["path"] == "tooling-showcase.service"
    assert all(item["requires_sudo"] is False for item in plan)


def test_uninstall_dry_run_shows_stop_when_service_is_active(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    config = _config(tmp_path)
    paths = linux_paths()
    paths.launcher.parent.mkdir(parents=True, exist_ok=True)
    paths.service.parent.mkdir(parents=True, exist_ok=True)
    paths.launcher.write_text("launcher", encoding="utf-8")
    paths.service.write_text("service", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    monkeypatch.setattr(linux_module, "_systemctl_path", lambda: "/usr/bin/systemctl")
    monkeypatch.setattr(linux_module, "_systemctl_value", lambda args, notes: "loaded")

    def fake_systemctl_ok(args, notes, quiet_expected=False):
        calls.append(tuple(args))
        return args == ["is-active", "--quiet", "tooling-showcase.service"]

    monkeypatch.setattr(linux_module, "_systemctl_ok", fake_systemctl_ok)

    result = linux_module.uninstall(config, dry_run=True).to_dict()

    assert result["dry_run"] is True
    assert "systemd_user_stop" in _plan_actions(result["plan"])
    assert ("stop", "tooling-showcase.service") not in calls
    assert paths.launcher.exists()
    assert paths.service.exists()


def test_uninstall_stops_active_user_service_before_removing_files(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    config = _config(tmp_path)
    paths = linux_paths()
    paths.launcher.parent.mkdir(parents=True, exist_ok=True)
    paths.service.parent.mkdir(parents=True, exist_ok=True)
    paths.launcher.write_text("launcher", encoding="utf-8")
    paths.service.write_text("service", encoding="utf-8")
    calls: list[tuple[str, ...]] = []
    state = {"active": True, "enabled": True}

    monkeypatch.setattr(linux_module, "_systemctl_path", lambda: "/usr/bin/systemctl")
    monkeypatch.setattr(linux_module, "_systemctl_value", lambda args, notes: "loaded" if paths.service.exists() else "not-found")

    def fake_systemctl_ok(args, notes, quiet_expected=False):
        calls.append(tuple(args))
        if args == ["is-active", "--quiet", "tooling-showcase.service"]:
            return state["active"]
        if args == ["is-enabled", "--quiet", "tooling-showcase.service"]:
            return state["enabled"]
        if args == ["stop", "tooling-showcase.service"]:
            state["active"] = False
            return True
        if args == ["disable", "tooling-showcase.service"]:
            state["enabled"] = False
            return True
        if args == ["daemon-reload"]:
            return True
        return False

    monkeypatch.setattr(linux_module, "_systemctl_ok", fake_systemctl_ok)

    result = linux_module.uninstall(config).to_dict()

    assert result["ok"] is True
    assert ("stop", "tooling-showcase.service") in calls
    assert calls.index(("stop", "tooling-showcase.service")) < calls.index(("disable", "tooling-showcase.service"))
    assert not paths.launcher.exists()
    assert not paths.service.exists()
    assert result["status"]["launcher_installed"] is False
    assert result["status"]["service_installed"] is False
    assert result["status"]["service_running"] is False
    assert result["status"]["autostart_enabled"] is False


def test_install_dry_run_does_not_write_desktop_files(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)
    paths = linux_paths()

    result = install_desktop(_config(tmp_path), dry_run=True).to_dict()

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["plan"]
    assert "systemd_user_enable" not in _plan_actions(result["plan"])
    assert not paths.launcher.exists()
    assert not paths.service.exists()


def test_autostart_install_dry_run_shows_enable_plan(tmp_path, monkeypatch):
    _isolate_home(tmp_path, monkeypatch)

    result = install_desktop(_config(tmp_path), dry_run=True, autostart=True).to_dict()

    assert result["dry_run"] is True
    assert "systemd_user_enable" in _plan_actions(result["plan"])


def test_windows_and_macos_future_addons_report_clearly(tmp_path):
    win = desktop_status(_config(tmp_path), platform_name="win32").to_dict()
    mac = desktop_status(_config(tmp_path), platform_name="darwin").to_dict()

    assert win["supported"] is True
    assert mac["supported"] is True
    assert win["tray_installed"] is False
    assert mac["protocol_handler_installed"] is False
    assert "not fully implemented" in " ".join(win["notes"])
    assert "not fully implemented" in " ".join(mac["notes"])


def test_cli_desktop_status_command_does_not_crash(tmp_path, monkeypatch, capsys):
    _isolate_cli(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", ["tooling-showcase", "desktop", "status", "--json"])

    code = main()
    output = capsys.readouterr().out
    data = json.loads(output)

    assert code == 0
    assert data["platform"] in {"linux", "windows", "macos"}
    assert "launcher_installed" in data


def test_cli_desktop_install_dry_run_command_does_not_write(tmp_path, monkeypatch, capsys):
    _isolate_cli(tmp_path, monkeypatch)
    paths = linux_paths()
    monkeypatch.setattr(sys, "argv", ["tooling-showcase", "desktop", "install", "--dry-run", "--json"])

    code = main()
    data = json.loads(capsys.readouterr().out)

    assert code == 0
    assert data["dry_run"] is True
    assert "systemd_user_enable" not in _plan_actions(data["plan"])
    assert not paths.launcher.exists()
    assert not paths.service.exists()


def test_cli_desktop_install_autostart_dry_run_shows_enable(tmp_path, monkeypatch, capsys):
    _isolate_cli(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", ["tooling-showcase", "desktop", "install", "--dry-run", "--autostart", "--json"])

    code = main()
    data = json.loads(capsys.readouterr().out)

    assert code == 0
    assert data["dry_run"] is True
    assert "systemd_user_enable" in _plan_actions(data["plan"])


def test_install_sh_desktop_only_modes_exit_before_normal_setup():
    script = Path("install.sh").read_text(encoding="utf-8")
    mode_block = script[script.index('if [[ "$DESKTOP_MODE" == "only"'):script.index('if ask_yes_no "Create or reuse .venv?"')]

    assert "run_showcase_cli desktop install" in mode_block
    assert "run_showcase_cli desktop repair" in mode_block
    assert "exit $?" in mode_block
    assert "Create or reuse .venv" not in mode_block


def _config(root: Path) -> ShowcaseConfig:
    root.mkdir(parents=True, exist_ok=True)
    return ShowcaseConfig(
        project_root=root,
        workspace_root=root,
        portfolio_root=root,
        journal_path=root / "state" / "events.jsonl",
        ollama=OllamaConfig(enabled=False),
        shell_policy=ShellPolicy(),
        benchmark_path=root / "state" / "model_benchmarks.json",
    )


def _isolate_home(tmp_path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))


def _isolate_cli(tmp_path, monkeypatch) -> None:
    _isolate_home(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOOLING_SHOWCASE_OLLAMA_ENABLED", "false")
    monkeypatch.setenv("TOOLING_SHOWCASE_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("TOOLING_SHOWCASE_PORTFOLIO", str(tmp_path))
    monkeypatch.setenv("TOOLING_SHOWCASE_JOURNAL", str(tmp_path / "state" / "events.jsonl"))
    monkeypatch.setenv("TOOLING_SHOWCASE_BENCHMARKS", str(tmp_path / "state" / "model_benchmarks.json"))


def _plan_actions(plan: list[dict]) -> set[str]:
    return {str(item.get("action", "")) for item in plan}
