from __future__ import annotations

import argparse
import json
from pathlib import Path

from tooling_showcase.benchmarking import benchmark_command
from tooling_showcase.config import load_config
from tooling_showcase.desktop import (
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
from tooling_showcase.doctor import run_doctor
from tooling_showcase.ollama_wrapper import run_ollama_wrapper
from tooling_showcase.research import ResearchLab
from tooling_showcase.service import ShowcaseService
from tooling_showcase.server import run_server
from tooling_showcase.tui import run_tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tooling-showcase")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_timeout_options(command: argparse.ArgumentParser) -> None:
        command.add_argument("--ollama-timeout", type=int, default=None, help="Ollama request timeout in seconds.")
        command.add_argument("--tool-timeout", type=int, default=None, help="Tool execution timeout in seconds.")

    def add_host_port(command: argparse.ArgumentParser) -> None:
        command.add_argument("--host", default="127.0.0.1", help="Local host to manage. Defaults to loopback.")
        command.add_argument("--port", type=int, default=8123, help="Local web UI port.")

    status_cmd = sub.add_parser("status", help="Show backend, Ollama, desktop, service, launcher, and platform status")
    add_host_port(status_cmd)
    status_cmd.add_argument("--json", action="store_true", help="Print machine-readable status JSON.")

    open_cmd = sub.add_parser("open", help="Open the local web UI in the system browser")
    add_host_port(open_cmd)
    open_cmd.add_argument("--no-start", action="store_true", help="Do not start the backend before opening the browser.")
    open_cmd.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    start_cmd = sub.add_parser("start", help="Start the local web UI backend using the user service or a managed process")
    add_host_port(start_cmd)
    start_cmd.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    stop_cmd = sub.add_parser("stop", help="Stop the local web UI backend if it is managed by this project")
    add_host_port(stop_cmd)
    stop_cmd.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    restart_cmd = sub.add_parser("restart", help="Restart the local web UI backend")
    add_host_port(restart_cmd)
    restart_cmd.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    logs_cmd = sub.add_parser("logs", help="Show backend and desktop integration log locations and recent entries")
    logs_cmd.add_argument("--lines", type=int, default=40, help="Recent lines to print from each log file.")
    logs_cmd.add_argument("--json", action="store_true", help="Print machine-readable logs JSON.")

    desktop = sub.add_parser("desktop", help="Manage optional desktop/system integration")
    desktop_sub = desktop.add_subparsers(dest="desktop_command", required=True)
    desktop_status_cmd = desktop_sub.add_parser("status", help="Show desktop integration status")
    desktop_status_cmd.add_argument("--json", action="store_true", help="Print machine-readable status JSON.")

    desktop_install = desktop_sub.add_parser("install", help="Install user-level desktop integration assets")
    desktop_install.add_argument("--dry-run", action="store_true", help="Show the install plan without writing files.")
    desktop_install.add_argument("--autostart", action="store_true", help="Enable the user service after installing. Disabled by default.")
    desktop_install.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    desktop_uninstall = desktop_sub.add_parser("uninstall", help="Remove project-owned desktop integration files")
    desktop_uninstall.add_argument("--dry-run", action="store_true", help="Show the uninstall plan without removing files.")
    desktop_uninstall.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    desktop_repair = desktop_sub.add_parser("repair", help="Reinstall or repair missing desktop integration files")
    desktop_repair.add_argument("--dry-run", action="store_true", help="Show the repair plan without writing files.")
    desktop_repair.add_argument("--autostart", action="store_true", help="Enable the user service after repairing. Disabled by default.")
    desktop_repair.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    desktop_logs = desktop_sub.add_parser("logs", help="Show desktop integration log locations and recent entries")
    desktop_logs.add_argument("--lines", type=int, default=40, help="Recent lines to print from each log file.")
    desktop_logs.add_argument("--json", action="store_true", help="Print machine-readable logs JSON.")

    desktop_open = desktop_sub.add_parser("open", help="Open the local web UI from desktop integration")
    add_host_port(desktop_open)
    desktop_open.add_argument("--no-start", action="store_true", help="Do not start the backend before opening the browser.")
    desktop_open.add_argument("--json", action="store_true", help="Print machine-readable action JSON.")

    ask = sub.add_parser("ask", help="Route a request through the showcase runtime")
    ask.add_argument("text")
    ask.add_argument("--confirm", action="store_true")
    ask.add_argument("--workspace", default=None)
    add_timeout_options(ask)

    journal = sub.add_parser("journal", help="Show recent immutable event records")
    journal.add_argument("--limit", type=int, default=10)

    sub.add_parser("adapters", help="Show detected workspace adapters")
    sub.add_parser("models", help="Show installed-model jobs and routing categories")

    benchmark = sub.add_parser("benchmark", help="Benchmark local Ollama models and derive routing profiles")
    benchmark.add_argument("--model", action="append", default=[], help="Model to benchmark. Can be repeated.")
    benchmark.add_argument("--all", action="store_true", help="Re-run every selected/installed model instead of only new models.")
    benchmark.add_argument("--limit-tasks", type=int, default=None, help="Limit task count for a smoke run.")
    benchmark.add_argument("--list-models", action="store_true", help="Print installed and unbenchmarked model inventory.")
    benchmark.add_argument("--shell-summary", action="store_true", help="Print shell-friendly inventory variables for install.sh.")

    doctor = sub.add_parser("doctor", help="Check local install, paths, static assets, and Ollama reachability")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable doctor output.")

    tui = sub.add_parser("tui", help="Run the terminal UI")
    tui.add_argument("--workspace", default=None)
    add_timeout_options(tui)

    serve = sub.add_parser("serve", help="Run the showcase web UI")
    serve.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host. Defaults to loopback; pass 0.0.0.0 only when you intentionally want LAN access.",
    )
    serve.add_argument("--port", type=int, default=8123)
    serve.add_argument("--workspace", default=None)
    serve.add_argument(
        "--enable-remote-tool-api",
        action="store_true",
        help="Allow /api/tool on non-loopback binds. Use only on trusted networks.",
    )
    add_timeout_options(serve)

    wrapper = sub.add_parser(
        "serve-ollama", help="Run an Ollama-compatible showcase wrapper"
    )
    wrapper.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host. Defaults to loopback; pass 0.0.0.0 only when you intentionally want LAN access.",
    )
    wrapper.add_argument("--port", type=int, default=11436)
    wrapper.add_argument("--workspace", default=None)
    add_timeout_options(wrapper)
    wrapper.add_argument(
        "--ollama-endpoint",
        default=None,
        help="Ollama endpoint (default: http://127.0.0.1:11434)",
    )

    research = sub.add_parser("research", help="Run a Research Lab session")
    research.add_argument("goal", help="Research goal or question.")
    research.add_argument("--mode", choices=["local", "hybrid"], default="local")
    research.add_argument("--depth", type=int, default=2)
    research.add_argument("--model", default="auto", help="Research model override (use auto for routing).")
    research.add_argument("--no-run", action="store_true", help="Only create the plan; do not gather sources.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path.cwd().resolve()
    config = load_config(root)
    if getattr(args, "workspace", None):
        config.workspace_root = Path(args.workspace).resolve()
    if getattr(args, "ollama_timeout", None) is not None:
        config.ollama.timeout_seconds = max(1, args.ollama_timeout)
    if getattr(args, "tool_timeout", None) is not None:
        config.shell_policy.timeout_seconds = max(1, args.tool_timeout)
    service = ShowcaseService(config)

    if args.command == "status":
        data = system_status(config, host=args.host, port=args.port)
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            _print_system_status(data)
        return 0

    if args.command == "open":
        result = open_local_ui(config, host=args.host, port=args.port, start_if_needed=not args.no_start)
        _print_action(result.to_dict(), json_output=args.json)
        return 0 if result.ok else 1

    if args.command == "start":
        result = start_backend(config, host=args.host, port=args.port)
        _print_action(result.to_dict(), json_output=args.json)
        return 0 if result.ok else 1

    if args.command == "stop":
        result = stop_backend(config, host=args.host, port=args.port)
        _print_action(result.to_dict(), json_output=args.json)
        return 0 if result.ok else 1

    if args.command == "restart":
        result = restart_backend(config, host=args.host, port=args.port)
        _print_action(result.to_dict(), json_output=args.json)
        return 0 if result.ok else 1

    if args.command == "logs":
        data = recent_logs(config, lines=args.lines)
        _print_logs(data, json_output=args.json)
        return 0

    if args.command == "desktop":
        if args.desktop_command == "status":
            data = desktop_status(config).to_dict()
            if args.json:
                print(json.dumps(data, indent=2, sort_keys=True))
            else:
                _print_desktop_status(data)
            return 0
        if args.desktop_command == "install":
            result = install_desktop(config, dry_run=args.dry_run, autostart=args.autostart)
            _print_action(result.to_dict(), json_output=args.json)
            return 0 if result.ok else 1
        if args.desktop_command == "uninstall":
            result = uninstall_desktop(config, dry_run=args.dry_run)
            _print_action(result.to_dict(), json_output=args.json)
            return 0 if result.ok else 1
        if args.desktop_command == "repair":
            result = repair_desktop(config, dry_run=args.dry_run, autostart=args.autostart)
            _print_action(result.to_dict(), json_output=args.json)
            return 0 if result.ok else 1
        if args.desktop_command == "logs":
            data = recent_logs(config, lines=args.lines)
            _print_logs(data, json_output=args.json)
            return 0
        if args.desktop_command == "open":
            result = open_local_ui(config, host=args.host, port=args.port, start_if_needed=not args.no_start)
            _print_action(result.to_dict(), json_output=args.json)
            return 0 if result.ok else 1

    if args.command == "ask":
        result = service.handle(args.text, confirm=args.confirm)
        model_route = (result.data or {}).get("model_route", {}) if result.data else {}
        if model_route.get("model"):
            print(
                f"[model] {model_route['model']} | {model_route.get('category', 'unknown')} | {model_route.get('job', '')}"
            )
        print(result.message)
        if result.tool_calls:
            print("\nTool calls:")
            for call in result.tool_calls:
                print(f"- {call.tool_name}: ok={str(call.ok).lower()}")
        return 0 if result.ok else 1

    if args.command == "journal":
        for event in service.recent_events(limit=args.limit):
            print(json.dumps(event, indent=2, sort_keys=True))
        return 0

    if args.command == "adapters":
        for card in service.adapter_cards():
            print(json.dumps(card, indent=2, sort_keys=True))
        return 0

    if args.command == "models":
        for card in service.model_cards():
            print(json.dumps(card, indent=2, sort_keys=True))
        return 0

    if args.command == "benchmark":
        return benchmark_command(config, args)

    if args.command == "doctor":
        return run_doctor(config, json_output=args.json)

    if args.command == "research":
        lab = ResearchLab(service)
        session = lab.start(args.goal, mode=args.mode, depth=args.depth, model=args.model)
        if not args.no_run:
            session = lab.run(session["id"])
        print(session.get("report") or json.dumps(session, indent=2, sort_keys=True))
        return 0 if session.get("status") != "failed" else 1

    if args.command == "tui":
        return run_tui(service)

    if args.command == "serve":
        return run_server(
            service,
            host=args.host,
            port=args.port,
            enable_remote_tool_api=args.enable_remote_tool_api,
        )

    if args.command == "serve-ollama":
        endpoint = args.ollama_endpoint or config.ollama.endpoint
        return run_ollama_wrapper(
            service,
            host=args.host,
            port=args.port,
            upstream_endpoint=endpoint,
        )

    return 2


def _print_system_status(data: dict) -> None:
    backend = data.get("backend", {})
    ollama = data.get("ollama", {})
    desktop = data.get("desktop", {})
    service = data.get("service", {})
    launcher = data.get("launcher", {})
    platform = data.get("platform", {})
    logs = data.get("logs", {})
    print(f"Backend: {'running' if backend.get('running') else 'stopped'} ({data.get('local_url')})")
    print(f"Configured port: {data.get('configured_port')}")
    print(f"Ollama: {ollama.get('state', 'unknown')} ({ollama.get('endpoint', 'not configured')})")
    print(f"Desktop integration: {desktop.get('state', 'unknown')} on {desktop.get('platform', 'unknown')}")
    print(f"Service: installed={service.get('installed')} running={service.get('running')} autostart={service.get('autostart_enabled')}")
    print(f"Launcher: installed={launcher.get('installed')} path={launcher.get('path')}")
    print(f"Platform: {platform.get('system')} {platform.get('release')} {platform.get('machine')}")
    print(f"Logs: {logs.get('logs_dir')}")
    for note in desktop.get("notes", []):
        print(f"Note: {note}")


def _print_desktop_status(data: dict) -> None:
    print(f"Desktop integration: {data.get('state', 'unknown')} ({data.get('platform', 'unknown')})")
    print(f"Supported: {data.get('supported')}")
    print(f"Launcher: installed={data.get('launcher_installed')} path={data.get('launcher_path')}")
    print(f"Service: installed={data.get('service_installed')} running={data.get('service_running')} autostart={data.get('autostart_enabled')}")
    print(f"Future add-ons: tray={data.get('tray_installed')} file_actions={data.get('file_actions_installed')} protocol_handler={data.get('protocol_handler_installed')}")
    print(f"Local URL: {data.get('local_url')}")
    print(f"Logs: {data.get('logs_path')}")
    for note in data.get("notes", []):
        print(f"Note: {note}")


def _print_action(data: dict, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    print(f"{data.get('action', 'action')}: {'ok' if data.get('ok') else 'failed'}")
    if data.get("dry_run"):
        print("Dry run: no files were changed.")
    for path in data.get("changed", []):
        print(f"Changed: {path}")
    for path in data.get("skipped", []):
        print(f"Skipped: {path}")
    for note in data.get("notes", []):
        print(f"Note: {note}")
    if data.get("plan"):
        print("Plan:")
        for item in data.get("plan", []):
            print(f"- {item.get('action')} {item.get('path') or ''} sudo={item.get('requires_sudo')}")


def _print_logs(data: dict, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    print(f"Logs path: {data.get('logs_path')}")
    for name, item in (data.get("logs") or {}).items():
        print(f"{name}: {item.get('path')} ({'exists' if item.get('exists') else 'missing'})")
        for line in item.get("lines", []):
            print(line)


if __name__ == "__main__":
    raise SystemExit(main())
