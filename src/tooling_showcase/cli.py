from __future__ import annotations

import argparse
import json
from pathlib import Path

from tooling_showcase.benchmarking import benchmark_command
from tooling_showcase.config import load_config
from tooling_showcase.ollama_wrapper import run_ollama_wrapper
from tooling_showcase.service import ShowcaseService
from tooling_showcase.server import run_server
from tooling_showcase.tui import run_tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tooling-showcase")
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="Route a request through the showcase runtime")
    ask.add_argument("text")
    ask.add_argument("--confirm", action="store_true")
    ask.add_argument("--workspace", default=None)

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

    tui = sub.add_parser("tui", help="Run the terminal UI")
    tui.add_argument("--workspace", default=None)

    serve = sub.add_parser("serve", help="Run the showcase web UI")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8123)
    serve.add_argument("--workspace", default=None)

    wrapper = sub.add_parser(
        "serve-ollama", help="Run an Ollama-compatible showcase wrapper"
    )
    wrapper.add_argument("--host", default="0.0.0.0")
    wrapper.add_argument("--port", type=int, default=11436)
    wrapper.add_argument("--workspace", default=None)
    wrapper.add_argument(
        "--ollama-endpoint",
        default=None,
        help="Ollama endpoint (default: http://127.0.0.1:11434)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    config = load_config(root)
    if getattr(args, "workspace", None):
        config.workspace_root = Path(args.workspace).resolve()
    service = ShowcaseService(config)

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

    if args.command == "tui":
        return run_tui(service)

    if args.command == "serve":
        return run_server(service, host=args.host, port=args.port)

    if args.command == "serve-ollama":
        endpoint = args.ollama_endpoint or config.ollama.endpoint
        return run_ollama_wrapper(
            service,
            host=args.host,
            port=args.port,
            upstream_endpoint=endpoint,
        )

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
