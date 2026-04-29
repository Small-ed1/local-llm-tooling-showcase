from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import os
import re
import shlex
import subprocess
import sys

from tooling_showcase.config import load_config
from tooling_showcase.ollama import OllamaClient
from tooling_showcase.service import ShowcaseService


HYPR_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "commands": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dispatch": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["dispatch"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["message", "commands"],
    "additionalProperties": False,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hyprland sidebar backend")
    parser.add_argument("command", choices=("status", "act"))
    parser.add_argument("request", nargs="?", default="")
    parser.add_argument("--model", default="")
    args = parser.parse_args(argv)

    if args.command == "status":
        _print_json(status_payload())
        return 0

    payload = act_payload(args.request, model=args.model or None)
    _print_json(payload)
    return 0 if payload.get("ok", False) else 1


def status_payload() -> dict[str, Any]:
    try:
        snapshot = hypr_snapshot()
    except RuntimeError as exc:
        return {"ok": False, "message": str(exc), "state": {}}
    return {"ok": True, "message": "Hypr state loaded.", "state": snapshot}


def act_payload(request: str, *, model: str | None = None) -> dict[str, Any]:
    request = request.strip()
    if not request:
        return {
            "ok": False,
            "message": "Request is empty.",
            "commands": [],
            "state": {},
        }

    try:
        snapshot = hypr_snapshot()
    except RuntimeError as exc:
        return {"ok": False, "message": str(exc), "commands": [], "state": {}}

    plan = direct_plan(request)
    if plan is None and _looks_like_desktop_control(request):
        plan = llm_plan(request, snapshot, model=model)

    if plan is None:
        return assistant_payload(request, model=model)

    commands = plan.get("commands", [])
    executed: list[dict[str, Any]] = []
    ok = True
    for command in commands:
        dispatch = str(command.get("dispatch", "")).strip()
        if not dispatch:
            continue
        try:
            summary = hypr_dispatch(dispatch)
            executed.append({"dispatch": dispatch, "ok": True, "summary": summary})
        except RuntimeError as exc:
            executed.append({"dispatch": dispatch, "ok": False, "summary": str(exc)})
            ok = False

    refreshed = snapshot
    try:
        refreshed = hypr_snapshot()
    except RuntimeError:
        pass

    return {
        "ok": ok,
        "message": str(plan.get("message", "Done.")).strip() or "Done.",
        "commands": executed,
        "state": refreshed,
    }


def assistant_payload(request: str, *, model: str | None = None) -> dict[str, Any]:
    config = _sidebar_config()
    service = ShowcaseService(config)
    result = service.handle(request, model=model)
    return {
        "ok": result.ok,
        "message": result.message,
        "commands": [
            {
                "dispatch": call.tool_name,
                "ok": call.ok,
                "summary": call.summary,
            }
            for call in result.tool_calls
        ],
        "state": {},
    }


def direct_plan(request: str) -> dict[str, Any] | None:
    lowered = request.lower().strip()

    workspace_match = re.search(r"(?:focus|switch to|go to) workspace (\d+)", lowered)
    if workspace_match:
        target = workspace_match.group(1)
        return {
            "message": f"Switching to workspace {target}.",
            "commands": [{"dispatch": f"workspace {target}"}],
        }

    move_match = re.search(
        r"(?:move|send) (?:the )?(?:active|current)? ?window to workspace (\d+)",
        lowered,
    )
    if move_match:
        target = move_match.group(1)
        return {
            "message": f"Moving the active window to workspace {target}.",
            "commands": [{"dispatch": f"movetoworkspace {target}"}],
        }

    launch_match = re.search(r"(?:launch|open|start|run) (.+)", request, re.IGNORECASE)
    if launch_match:
        target = launch_match.group(1).strip()
        if target:
            return {
                "message": f"Launching {target}.",
                "commands": [{"dispatch": f"exec {target}"}],
            }

    if "close active" in lowered or "close window" in lowered:
        return {
            "message": "Closing the active window.",
            "commands": [{"dispatch": "closewindow"}],
        }

    if "toggle floating" in lowered or "float this" in lowered:
        return {
            "message": "Toggling floating for the active window.",
            "commands": [{"dispatch": "togglefloating active"}],
        }

    if "toggle fullscreen" in lowered or "fullscreen" == lowered:
        return {
            "message": "Toggling fullscreen for the active window.",
            "commands": [{"dispatch": "fullscreen 0"}],
        }

    if lowered in {"reload hypr", "reload hyprland", "reload config"}:
        return {
            "message": "Reloading Hyprland.",
            "commands": [{"dispatch": "exec hyprctl reload"}],
        }

    return None


def _looks_like_desktop_control(request: str) -> bool:
    lowered = request.lower().strip()
    return any(
        phrase in lowered
        for phrase in (
            "workspace",
            "window",
            "focus ",
            "move ",
            "send ",
            "launch ",
            "open ",
            "start ",
            "close ",
            "fullscreen",
            "floating",
            "hypr",
            "monitor",
        )
    )


def llm_plan(
    request: str, snapshot: dict[str, Any], *, model: str | None = None
) -> dict[str, Any]:
    config = _sidebar_config()
    client = OllamaClient(config.ollama)
    prompt = build_planner_prompt(request, snapshot)
    result = client.ask(
        prompt,
        response_format=HYPR_PLAN_SCHEMA,
        model=model,
        system_prompt=(
            "You are a Hyprland action planner. Output only valid JSON matching the requested schema. "
            "Use Hyprland dispatch commands only. Prefer short safe command lists."
        ),
    )
    if not result.ok:
        return {"message": result.message, "commands": []}
    try:
        payload = json.loads(result.message)
    except json.JSONDecodeError:
        return {"message": result.message, "commands": []}
    if not isinstance(payload, dict):
        return {"message": "Planner returned invalid payload.", "commands": []}
    commands = payload.get("commands")
    if not isinstance(commands, list):
        payload["commands"] = []
    return payload


def build_planner_prompt(request: str, snapshot: dict[str, Any]) -> str:
    lines = [
        "You are planning Hyprland commands for a floating assistant sidebar.",
        "Allowed output: JSON only.",
        "Each command must be a valid `hyprctl dispatch ...` payload without the leading `hyprctl dispatch` words.",
        "Examples: `workspace 3`, `movetoworkspace 2`, `focuswindow address:0x123`, `exec foot`.",
        "Do not use destructive shell chains.",
        "",
        f"Request:\n{request}",
        "",
        "Hypr snapshot:",
        summarize_snapshot(snapshot),
    ]
    return "\n".join(lines)


def summarize_snapshot(snapshot: dict[str, Any]) -> str:
    workspaces = snapshot.get("workspaces", [])
    clients = snapshot.get("clients", [])
    active = snapshot.get("active_window") or {}
    rows = [
        "Workspaces:",
        *[
            f"- id={item.get('id')} name={item.get('name')} windows={item.get('windows')} focused={item.get('focused')}"
            for item in workspaces
        ],
        "Active window:",
        f"- title={active.get('title', '')} class={active.get('class', '')} workspace={active.get('workspace', '')} address={active.get('address', '')}",
        "Clients:",
        *[
            f"- title={item.get('title')} class={item.get('class')} workspace={item.get('workspace')} address={item.get('address')}"
            for item in clients[:20]
        ],
    ]
    return "\n".join(rows)


def hypr_snapshot() -> dict[str, Any]:
    if "HYPRLAND_INSTANCE_SIGNATURE" not in os.environ:
        raise RuntimeError("Hyprland is not running in this environment.")
    workspaces_raw = hyprctl_json("workspaces")
    clients_raw = hyprctl_json("clients")
    active_raw = hyprctl_json("activewindow")
    return {
        "workspaces": [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "windows": item.get("windows", 0),
                "focused": bool(item.get("focused", False)),
            }
            for item in workspaces_raw
        ],
        "clients": [
            {
                "title": item.get("title", ""),
                "class": item.get("class", ""),
                "workspace": (item.get("workspace") or {}).get("id"),
                "address": item.get("address", ""),
            }
            for item in clients_raw
        ],
        "active_window": {
            "title": active_raw.get("title", ""),
            "class": active_raw.get("class", ""),
            "workspace": (active_raw.get("workspace") or {}).get("id"),
            "address": active_raw.get("address", ""),
        },
    }


def hyprctl_json(topic: str) -> Any:
    try:
        result = subprocess.run(
            ["hyprctl", "-j", topic],
            check=True,
            text=True,
            capture_output=True,
        )
    except (
        subprocess.CalledProcessError
    ) as exc:  # pragma: no cover - system integration
        raise RuntimeError(
            exc.stderr.strip() or exc.stdout.strip() or str(exc)
        ) from exc
    return json.loads(result.stdout)


def hypr_dispatch(dispatch: str) -> str:
    try:
        result = subprocess.run(
            ["hyprctl", "dispatch", *shlex.split(dispatch)],
            check=True,
            text=True,
            capture_output=True,
        )
    except (
        subprocess.CalledProcessError
    ) as exc:  # pragma: no cover - system integration
        raise RuntimeError(
            exc.stderr.strip() or exc.stdout.strip() or str(exc)
        ) from exc
    return result.stdout.strip() or f"dispatched {dispatch}"


def _print_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _sidebar_config():
    root = Path(os.getenv("TOOLING_SHOWCASE_ROOT", str(Path.cwd()))).resolve()
    return load_config(root)


if __name__ == "__main__":
    raise SystemExit(main())
