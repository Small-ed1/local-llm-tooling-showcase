from __future__ import annotations

from typing import Any

from tooling_showcase.models import ActionResult, ToolCall


class DirectFallbackMixin:
    def _deterministic_tool_route(
        self,
        text: str,
        *,
        confirm: bool,
        model: str,
        model_route: dict[str, Any],
        available_tools: list[str],
        tool_timeout_seconds: int | None,
    ) -> ActionResult | None:
        decision = self.router.route(text)
        if decision.route != "tool" or not decision.action:
            return None
        if decision.action not in available_tools:
            return None
        if decision.action == "shell_command":
            command = str((decision.arguments or {}).get("command", "")).strip().lower()
            if command in {"command", "a command", "shell command", "a shell command"}:
                return None

        call = self.tools.run_tool(decision.action, decision.arguments or {}, confirm=confirm, timeout_seconds=tool_timeout_seconds)
        return ActionResult(
            ok=call.ok,
            message=call.summary,
            data={
                "model": model,
                "model_route": model_route,
                "router": {
                    "route": decision.route,
                    "reason": decision.reason,
                    "action": decision.action,
                },
            },
            tool_calls=[call],
        )

    def _legacy_direct_tool_fallback(
        self,
        text: str,
        *,
        confirm: bool = False,
        tool_timeout_seconds: int | None = None,
    ) -> ActionResult | None:
        lowered = text.strip().lower()

        tool_call: ToolCall | None = None

        if lowered.startswith(("find file ", "search files ")):
            query = text.split(maxsplit=2)[-1]
            tool_call = self.tools.run_tool("file_search", {"query": query}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        elif lowered.startswith(("read file ", "inspect file ", "summarize file ")):
            path_text = text.split(maxsplit=2)[-1]
            tool_call = self.tools.run_tool("read_file", {"path_text": path_text}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        elif lowered.startswith(("search content ", "grep ", "find text ")):
            query = text.split(maxsplit=2)[-1]
            tool_call = self.tools.run_tool("content_search", {"query": query}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        elif lowered.startswith(("build index", "index project", "index files")):
            tool_call = self.tools.run_tool("build_index", {}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        elif lowered.startswith(("query index ", "search index ")):
            query = text.split(maxsplit=2)[-1]
            tool_call = self.tools.run_tool("query_index", {"query": query}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        elif lowered.startswith(("show tree", "tree view", "project tree")) or any(
            phrase in lowered for phrase in ("project structure", "show me the structure", "look around")
        ):
            tool_call = self.tools.run_tool("tree_view", {"path": ".", "max_depth": 4}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        elif lowered.startswith(("show adapters", "adapter inventory")) or "adapter" in lowered:
            tool_call = self.tools.run_tool("adapter_inventory", {}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        elif lowered.startswith(("run ", "shell ")):
            command = text.removeprefix("run ").removeprefix("shell ").strip()
            tool_call = self.tools.run_tool("shell_command", {"command": command}, confirm=confirm, timeout_seconds=tool_timeout_seconds)

        if tool_call is None:
            return None

        return ActionResult(
            ok=tool_call.ok,
            message=tool_call.summary,
            tool_calls=[tool_call],
            data={"fallback": "legacy_direct_tool_fallback_no_ollama"},
        )
