from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import inspect
import json
from typing import Any

from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.journal import EventJournal
from tooling_showcase.benchmarking import benchmark_profiles, default_benchmark_path, load_benchmark_results
from tooling_showcase.model_routing import route_model
from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.ollama import OllamaClient
from tooling_showcase.router import IntentRouter
from tooling_showcase.tool_protocol import (
    TOOL_SCHEMAS,
    compact_tool_result,
    normalize_tool_arguments,
    parse_model_json,
    tool_schema_text,
)
from tooling_showcase.tools import ToolRuntime


class ShowcaseService:
    def __init__(self, config: ShowcaseConfig) -> None:
        self.config = config
        self.router = IntentRouter()
        self.tools = ToolRuntime(config)
        self.ollama = OllamaClient(config.ollama)
        self.journal = EventJournal(config.journal_path)
        self.adapters = self.tools.adapters

    def handle(
        self,
        text: str,
        *,
        confirm: bool = False,
        model: str | None = None,
        system_prompt: str | None = None,
        options: dict[str, Any] | None = None,
        ollama_options: dict[str, Any] | None = None,
        response_format: str | dict | None = None,
        stream: bool = False,
        allow_tools: bool = True,
        max_tool_calls: int = 4,
        show_tool_traces: bool = False,
        ollama_timeout_seconds: int | None = None,
        tool_timeout_seconds: int | None = None,
    ) -> ActionResult:
        """
        Chat-first request handler.

        The user does NOT call tools directly.
        The model decides whether a tool is needed.
        The backend only validates and executes real registered tools.
        """
        text = text.strip()
        if not text:
            return ActionResult(False, "Empty message.")

        model_route = route_model(text)
        model_route_data = model_route.as_dict()
        requested_model = self._normalize_model_choice(model)
        if requested_model is None:
            model_route_data = self._route_with_benchmark_profile(model_route_data)
        selected_model = requested_model or str(model_route_data.get("model") or model_route.profile.model)
        selected_options = self._merge_options(options or ollama_options)
        enable_thinking, clean_options = self._extract_think(selected_options)
        selected_options = clean_options
        enable_thinking = enable_thinking and self._supports_thinking(selected_model)

        available_tools = self.tools.available_tools()
        planner_tools = [name for name in available_tools if name in TOOL_SCHEMAS]
        tool_calls: list[ToolCall] = []
        tool_context: list[str] = []

        if allow_tools:
            direct = self._deterministic_tool_route(
                text,
                confirm=confirm,
                model=selected_model,
                model_route=model_route_data,
                available_tools=available_tools,
                tool_timeout_seconds=tool_timeout_seconds,
            )
            if direct is not None:
                self._log_chat(
                    text=text,
                    result=direct,
                    model=selected_model,
                    model_route=model_route_data,
                    tool_calls=direct.tool_calls,
                    mode="deterministic_tool_route",
                )
                return direct

        if allow_tools and not self.config.ollama.enabled:
            legacy = self._legacy_direct_tool_fallback(text, confirm=confirm, tool_timeout_seconds=tool_timeout_seconds)
            if legacy is not None:
                self._log_chat(
                    text=text,
                    result=legacy,
                    model=selected_model,
                    model_route=model_route_data,
                    tool_calls=legacy.tool_calls,
                    mode="legacy_direct_tool_fallback_no_ollama",
                )
                return legacy

            result = ActionResult(False, "Local Ollama fallback is disabled.")
            result.data = {
                "model": selected_model,
                "model_route": model_route_data,
            }
            self.journal.append(
                {
                    "route": "llm_fallback",
                    "request": text,
                    "ok": result.ok,
                    "message": result.message,
                }
            )
            return result

        if not allow_tools:
            result = self._answer_direct(
                text,
                model=selected_model,
                system_prompt=system_prompt,
                options=selected_options,
                response_format=response_format,
                model_route=model_route_data,
                think=enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
            )
            self._log_chat(
                text=text,
                result=result,
                model=selected_model,
                model_route=model_route_data,
                tool_calls=[],
                mode="chat_no_tools",
            )
            return result

        contextual_calls = self.tools.maybe_contextual_tool_calls(text)
        if any(call.tool_name == "web_search" and call.ok for call in contextual_calls):
            result = self._answer_with_context(
                user_text=text,
                tool_context=[compact_tool_result(call) for call in contextual_calls],
                model=selected_model,
                system_prompt=system_prompt,
                options=selected_options,
                response_format=response_format,
                model_route=model_route_data,
                show_tool_traces=show_tool_traces,
                think=enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
            )
            result.tool_calls.extend(contextual_calls)
            self._log_chat(
                text=text,
                result=result,
                model=selected_model,
                model_route=model_route_data,
                tool_calls=contextual_calls,
                mode="contextual_web_answer",
            )
            return result

        if not self._likely_needs_tools(text):
            result = self._answer_direct(
                text,
                model=selected_model,
                system_prompt=system_prompt,
                options=selected_options,
                response_format=response_format,
                model_route=model_route_data,
                think=enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
            )
            self._log_chat(
                text=text,
                result=result,
                model=selected_model,
                model_route=model_route_data,
                tool_calls=[],
                mode="chat_direct_no_tool_signals",
            )
            return result

        executed_signatures: set[tuple[str, str]] = set()
        for step_index in range(max_tool_calls):
            decision_result = self._ask_ollama(
                self._build_tool_decision_prompt(
                    user_text=text,
                    available_tools=planner_tools,
                    previous_tool_context=tool_context,
                    step_index=step_index,
                    max_tool_calls=max_tool_calls,
                ),
                model=selected_model,
                system_prompt=self._tool_decision_system_prompt(system_prompt),
                response_format="json",
                options=selected_options,
                think=False,
                stream=False,
                timeout_seconds=ollama_timeout_seconds,
            )

            if not decision_result.ok:
                result = ActionResult(
                    False,
                    f"Tool decision model call failed: {decision_result.message}",
                    data={
                        "model": selected_model,
                        "model_route": model_route_data,
                    },
                    tool_calls=tool_calls,
                )
                self._log_chat(
                    text=text,
                    result=result,
                    model=selected_model,
                    model_route=model_route_data,
                    tool_calls=tool_calls,
                    mode="tool_decision_failed",
                )
                return result

            try:
                decision = parse_model_json(decision_result.message)
            except Exception as exc:
                fallback = self._answer_with_context(
                    user_text=text,
                    tool_context=tool_context,
                    model=selected_model,
                    system_prompt=system_prompt,
                    options=selected_options,
                    response_format=response_format,
                    model_route=model_route_data,
                    show_tool_traces=show_tool_traces,
                    think=enable_thinking,
                    recovery_note=f"The tool planner returned invalid JSON: {exc}",
                    ollama_timeout_seconds=ollama_timeout_seconds,
                )
                fallback.tool_calls.extend(tool_calls)
                self._log_chat(
                    text=text,
                    result=fallback,
                    model=selected_model,
                    model_route=model_route_data,
                    tool_calls=tool_calls,
                    mode="invalid_tool_json_recovered",
                )
                return fallback

            action = str(decision.get("action") or decision.get("type") or "").strip().lower()

            if action == "answer":
                answer_text = str(decision.get("answer") or decision.get("message") or "").strip()
                if decision.get("message") and "<END_OF_MESSAGE>" not in answer_text:
                    continue
                if answer_text and self._requires_tree_context(text) and not any(call.tool_name == "tree_view" for call in tool_calls):
                    call = self.tools.run_tool("tree_view", {"path": ".", "max_depth": 4}, confirm=confirm, timeout_seconds=tool_timeout_seconds)
                    tool_calls.append(call)
                    tool_context.append(compact_tool_result(call))
                    continue
                if answer_text and not enable_thinking and response_format is None:
                    answer_text = self._strip_loop_end_marker(answer_text)
                    result = ActionResult(
                        True,
                        answer_text,
                        data={
                            "model": selected_model,
                            "model_route": model_route_data,
                            "planner": decision,
                        },
                        tool_calls=tool_calls,
                    )
                    self._log_chat(
                        text=text,
                        result=result,
                        model=selected_model,
                        model_route=model_route_data,
                        tool_calls=tool_calls,
                        mode="model_answered_without_more_tools",
                    )
                    return result

                break

            if action != "tool_call":
                tool_context.append(
                    "Planner returned an unknown action. Valid actions are answer or tool_call."
                )
                continue

            tool_name = str(decision.get("tool_name", "")).strip()
            arguments = decision.get("arguments") or {}
            if not isinstance(arguments, dict):
                arguments = {}

            normalized_args = normalize_tool_arguments(tool_name, arguments)
            signature = (tool_name, json.dumps(normalized_args, sort_keys=True, default=str))
            if signature in executed_signatures:
                tool_context.append(
                    f"Skipped duplicate tool call: {tool_name} {json.dumps(normalized_args, sort_keys=True, default=str)}"
                )
                continue

            if tool_name not in planner_tools:
                bad_call = ToolCall(
                    tool_name=tool_name or "unknown",
                    ok=False,
                    summary=(
                        "Rejected model-requested tool. Tool is not available to the chat planner. "
                        f"Available planner tools: {', '.join(planner_tools)}"
                    ),
                    data={"requested_tool": tool_name, "available_tools": planner_tools},
                )
                tool_calls.append(bad_call)
                tool_context.append(compact_tool_result(bad_call))
                continue

            safe_auto_run = self._safe_auto_run(tool_name)
            if not safe_auto_run and not confirm:
                blocked = ToolCall(
                    tool_name=tool_name,
                    ok=False,
                    summary=(
                        "Tool requires confirmation before running. "
                        "Ask the user for confirmation or rerun with confirm=true."
                    ),
                    data={"arguments": arguments, "requires_confirmation": True},
                )
                tool_calls.append(blocked)
                tool_context.append(compact_tool_result(blocked))
                break

            call = self.tools.run_tool(tool_name, normalized_args, confirm=confirm, timeout_seconds=tool_timeout_seconds)
            executed_signatures.add(signature)
            tool_calls.append(call)
            tool_context.append(compact_tool_result(call))

            continue

        result = self._answer_with_context(
            user_text=text,
            tool_context=tool_context,
            model=selected_model,
            system_prompt=system_prompt,
            options=selected_options,
            response_format=response_format,
            model_route=model_route_data,
            show_tool_traces=show_tool_traces,
            think=enable_thinking,
            ollama_timeout_seconds=ollama_timeout_seconds,
        )
        result.tool_calls.extend(tool_calls)

        self._log_chat(
            text=text,
            result=result,
            model=selected_model,
            model_route=model_route_data,
            tool_calls=tool_calls,
            mode="model_tool_loop",
        )
        return result

    def recent_events(self, limit: int = 10) -> list[dict]:
        return self.journal.tail(limit)

    def adapter_cards(self) -> list[dict]:
        return [asdict(card) for card in self.adapters.cards()]

    def model_cards(self) -> list[dict]:
        benchmark_path = default_benchmark_path(self.config)
        results = load_benchmark_results(benchmark_path)
        profiles = benchmark_profiles(benchmark_path)
        if profiles:
            return profiles
        return [
            {
                "model": model,
                "category": "unprofiled",
                "job": "run tooling-showcase benchmark to assign this model",
                "summary": "No local benchmark profile has been recorded yet.",
                "chat_capable": True,
            }
            for model in sorted(results.get("models", {}))
        ]

    def _route_with_benchmark_profile(self, route: dict[str, Any]) -> dict[str, Any]:
        profiles = benchmark_profiles(default_benchmark_path(self.config))
        if not profiles:
            return route
        category = str(route.get("category") or "general")
        profile = next((item for item in profiles if item.get("category") == category), None)
        if profile is None and category == "fast":
            profile = next((item for item in profiles if item.get("category") == "general"), None)
        if profile is None:
            return route
        updated = dict(route)
        updated.update(profile)
        updated["reason"] = f"{route.get('reason', 'Auto-routed request')} Selected from local benchmark profile for {profile.get('category')} work."
        updated["benchmark_profile"] = True
        return updated

    def run_tool_manual(
        self,
        name: str,
        arguments: dict | None = None,
        *,
        confirm: bool = False,
        timeout_seconds: int | None = None,
    ) -> ToolCall:
        """
        Developer/debug escape hatch only.
        Do not expose this as the primary chat UX.
        """
        return self.tools.run_tool(name, arguments or {}, confirm=confirm, timeout_seconds=timeout_seconds)

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

    def _answer_direct(
        self,
        text: str,
        *,
        model: str,
        system_prompt: str | None,
        options: dict[str, Any],
        response_format: str | dict | None,
        model_route: dict[str, Any],
        think: bool = False,
        ollama_timeout_seconds: int | None = None,
    ) -> ActionResult:
        result = self._ask_ollama(
            text,
            model=model,
            system_prompt=system_prompt,
            response_format=response_format,
            options=options,
            think=think,
            stream=False,
            timeout_seconds=ollama_timeout_seconds,
        )
        if response_format is None:
            result.message = self._normalize_answer_text(result.message)
        result.data = {
            **(result.data or {}),
            "model": model,
            "model_route": model_route,
        }
        return result

    def _normalize_answer_text(self, message: str) -> str:
        try:
            payload = parse_model_json(message)
        except Exception:
            return self._strip_loop_end_marker(message)
        answer = payload.get("answer") or payload.get("message")
        if isinstance(answer, str) and answer.strip():
            return self._strip_loop_end_marker(answer)
        return self._strip_loop_end_marker(message)

    def _answer_with_context(
        self,
        *,
        user_text: str,
        tool_context: list[str],
        model: str,
        system_prompt: str | None,
        options: dict[str, Any],
        response_format: str | dict | None,
        model_route: dict[str, Any],
        show_tool_traces: bool,
        think: bool = False,
        recovery_note: str | None = None,
        ollama_timeout_seconds: int | None = None,
    ) -> ActionResult:
        prompt = self._build_final_prompt(
            user_text=user_text,
            tool_context=tool_context,
            show_tool_traces=show_tool_traces,
            recovery_note=recovery_note,
        )
        result = self._ask_ollama(
            prompt,
            model=model,
            system_prompt=system_prompt,
            response_format=response_format,
            options=options,
            think=think,
            stream=False,
            timeout_seconds=ollama_timeout_seconds,
        )
        result.data = {
            **(result.data or {}),
            "model": model,
            "model_route": model_route,
            "tool_steps": len(tool_context),
        }
        return result

    def _build_tool_decision_prompt(
        self,
        *,
        user_text: str,
        available_tools: list[str],
        previous_tool_context: list[str],
        step_index: int,
        max_tool_calls: int,
    ) -> str:
        context = "\n\n".join(previous_tool_context).strip()
        if not context:
            context = "No tools have been called yet."

        return f"""
You are controlling tool use for a local chat assistant.

The user is chatting normally. They are NOT asking to manually operate a tool panel.
You decide whether to answer directly or request exactly one tool call.

Rules:
- Use tools only when they improve correctness.
- For latest/current/public information, use web_search.
- After web_search, if an official/primary result is available and the answer depends on exact current facts, call expand_search_result before answering.
- For local project files, search before reading unless the exact path is obvious.
- For project structure, repository layout, or "look around" requests, use tree_view.
- For shell_command, only use it when the user explicitly asks to run/inspect something locally.
- Never invent tool names. You may only choose from the provided tools.
- Do not explain your decision in prose. Return JSON only.

Step: {step_index + 1} of {max_tool_calls}

Current date:
{self._current_date_context()}

Available tools:
{tool_schema_text(available_tools)}

Previous tool results:
{context}

User message:
{user_text}

Return exactly one JSON object in one of these forms:

{{
  "action": "answer",
  "answer": "Final answer to the user."
}}

or

{{
  "action": "tool_call",
  "tool_name": "name_from_available_tools",
  "arguments": {{
    "query": "the user's search query"
  }},
  "reason": "Brief internal reason."
}}
""".strip()

    def _build_final_prompt(
        self,
        *,
        user_text: str,
        tool_context: list[str],
        show_tool_traces: bool,
        recovery_note: str | None,
    ) -> str:
        context = "\n\n".join(tool_context).strip()
        if not context:
            context = "No tool results were used."

        trace_rule = (
            "Include a compact 'Tool activity' section if useful."
            if show_tool_traces
            else "Do not dump raw tool logs. Mention tool use only when it helps clarity."
        )

        note = f"\nRecovery note: {recovery_note}\n" if recovery_note else ""

        return f"""
Answer the user as a normal chat assistant.

User message:
{user_text}

Tool results available to you:
{context}
{note}
Instructions:
- Use the tool results when they are relevant.
- If tool results are search titles/links only and do not contain enough evidence, consider using expand_search_result to fetch the official source.
- Prefer official/primary sources (kernel.org, docs.python.org, GitHub releases, official documentation) over blogs or SEO-optimized articles.
- Do not infer facts from search-result titles alone - fetch and verify from the actual page when in doubt.
- If a tool failed, explain the useful part without pretending it succeeded.
- Keep the answer user-facing and natural.
- {trace_rule}
""".strip()

    def _tool_decision_system_prompt(self, user_system_prompt: str | None) -> str:
        base = """
You are the tool-use planner for a local-first chat assistant.
You output JSON only.
Do not roleplay.
Do not answer with markdown.
Do not invent tool names.
Background capability note: files, code search, web search, shell, git, indexing, memory, and related tools are available capabilities.
Do not describe yourself as a package, wrapper, showcase assistant, or local tooling runtime unless the user explicitly asks.
""".strip()
        if user_system_prompt:
            return base + "\n\nUser/system style context for final answers, not tool JSON:\n" + user_system_prompt
        return base

    def _safe_auto_run(self, tool_name: str) -> bool:
        return bool(TOOL_SCHEMAS.get(tool_name, {}).get("safe_auto_run", False))

    def _requires_tree_context(self, text: str) -> bool:
        lowered = text.lower()
        return any(
            phrase in lowered
            for phrase in (
                "project structure",
                "repo structure",
                "repository structure",
                "directory structure",
                "folder structure",
                "tree view",
                "show me the structure",
                "look around this project",
                "summarize this project structure",
            )
        )

    def _likely_needs_tools(self, text: str) -> bool:
        lowered = text.lower()
        tool_signals = (
            "readme",
            "pyproject",
            "file",
            "files",
            "directory",
            "folder",
            "repo",
            "repository",
            "project structure",
            "codebase",
            "workspace",
            "adapter",
            "write ",
            "create ",
            "append ",
            ".txt",
            ".md",
            ".py",
            "path",
            "git ",
            "shell",
            "terminal",
            "command",
            "pytest",
            "run tests",
            "build project",
            "lint",
            "format code",
            "index",
            "library",
            "journal",
            "logs",
            "weather",
            "forecast",
            "temperature",
            "web",
            "online",
            "search",
            "look up",
            "docs",
            "documentation",
            "memory",
            "memories",
            "remember",
            "recall",
            "forget",
            "save this",
            "store this",
            "latest",
            "current",
            "today",
            "release",
            "version",
            "url",
            "http://",
            "https://",
        )
        return any(signal in lowered for signal in tool_signals)

    def _merge_options(self, options: dict[str, Any] | None) -> dict[str, Any]:
        merged: dict[str, Any] = {"temperature": self.config.ollama.temperature}
        if options:
            for key, value in options.items():
                if value is not None and value != "":
                    merged[key] = value
        return merged

    def _normalize_model_choice(self, model: str | None) -> str | None:
        if model is None:
            return None
        value = str(model).strip()
        if not value or value.lower() in {"none", "null", "auto", "default"}:
            return None
        return value

    def _supports_thinking(self, model: str) -> bool:
        return "qwen3" in model.lower()

    def _extract_think(self, options: dict[str, Any] | None) -> tuple[bool, dict[str, Any]]:
        clean_options = dict(options or {})
        think = bool(
            clean_options.pop("enable_thinking", False)
            or clean_options.pop("think", False)
        )
        return think, clean_options

    def _strip_loop_end_marker(self, message: str) -> str:
        return message.replace("<END_OF_MESSAGE>", "").strip()

    def _current_date_context(self) -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def _log_chat(
        self,
        *,
        text: str,
        result: ActionResult,
        model: str,
        model_route: dict[str, Any],
        tool_calls: list[ToolCall],
        mode: str,
    ) -> None:
        self.journal.append(
            {
                "route": "chat_model_directed_tools",
                "mode": mode,
                "request": text,
                "ok": result.ok,
                "message": result.message,
                "model": model,
                "model_route": model_route,
                "tool_calls": [asdict(call) for call in tool_calls],
            }
        )

    def _ask_ollama(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
        response_format: str | dict | None = None,
        options: dict | None = None,
        stream: bool = False,
        think: bool = False,
        timeout_seconds: int | None = None,
    ):
        signature = inspect.signature(self.ollama.ask)
        params = signature.parameters
        accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values())
        kwargs = {
            "model": model,
            "system_prompt": system_prompt,
            "response_format": response_format,
            "options": options,
            "stream": stream,
            "think": think,
            "timeout_seconds": timeout_seconds,
        }
        accepted = {
            key: value
            for key, value in kwargs.items()
            if value is not None and (accepts_kwargs or key in params)
        }
        return self.ollama.ask(prompt, **accepted)

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

    def _build_tool_choice_prompt(self, user_text: str, *args, **kwargs) -> str:
        return self._build_tool_decision_prompt(
            user_text=user_text,
            available_tools=kwargs.get("available_tools", self.tools.available_tools()),
            previous_tool_context=kwargs.get("previous_tool_context", []),
            step_index=kwargs.get("step_index", 0),
            max_tool_calls=kwargs.get("max_tool_calls", 4),
        )

    def run_autonomous(
        self,
        goal: str,
        *,
        max_steps: int = 5,
        confirm: bool = False,
    ) -> ActionResult:
        steps = [f"autonomous_step_{index + 1}" for index in range(max_steps)]
        plan_result = self.tools.plan_task(goal, steps)
        if not plan_result.ok:
            return ActionResult(False, f"Failed to plan task: {plan_result.summary}", tool_calls=[plan_result])

        task_id = str((plan_result.data or {}).get("task_id", ""))
        calls = [plan_result]
        for step_num in range(max_steps):
            execute_result = self.tools.execute_step(task_id, step_num)
            calls.append(execute_result)
            if not execute_result.ok:
                break
            step_result = self.handle(
                goal,
                confirm=confirm,
                allow_tools=True,
                max_tool_calls=1,
                show_tool_traces=True,
            )
            calls.extend(step_result.tool_calls)
            calls.append(self.tools.mark_step_complete(task_id, step_num))

        status_result = self.tools.get_task_status(task_id)
        calls.append(status_result)
        result = ActionResult(
            status_result.ok,
            f"Autonomous run completed: {goal}",
            data={"autonomous": True, "max_steps": max_steps, "task_id": task_id},
            tool_calls=calls,
        )
        return result
