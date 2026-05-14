from __future__ import annotations

from dataclasses import asdict
import inspect
from typing import Any

from tooling_showcase.benchmarking import benchmark_profiles, default_benchmark_path, list_ollama_models, load_benchmark_results
from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.journal import EventJournal
from tooling_showcase.model_routing import route_model
from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.ollama import OllamaClient
from tooling_showcase.router import IntentRouter
from tooling_showcase.service_fallbacks import DirectFallbackMixin
from tooling_showcase.service_planner import PlannerLoopMixin
from tooling_showcase.service_prompts import (
    PromptFormattingMixin,
    conversation_history_text as _conversation_history_text,
    has_contextual_reference as _has_contextual_reference,
    normalize_chat_messages as _normalize_chat_messages,
    replace_last_user_message as _replace_last_user_message,
)
from tooling_showcase.service_streaming import StreamingResponseMixin
from tooling_showcase.tool_protocol import TOOL_SCHEMAS, compact_tool_result
from tooling_showcase.tools import ToolRuntime


class ShowcaseService(
    PromptFormattingMixin,
    DirectFallbackMixin,
    PlannerLoopMixin,
    StreamingResponseMixin,
):
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
        messages: list[dict[str, Any]] | None = None,
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

        chat_messages = _normalize_chat_messages(messages, text)
        tool_signal_text = f"{_conversation_history_text(chat_messages)}\n\nCurrent user message: {text}" if _has_contextual_reference(text) else text

        model_route = route_model(text)
        model_route_data = model_route.as_dict()
        requested_model = self._normalize_model_choice(model)
        if requested_model is None:
            model_route_data = self._route_with_benchmark_profile(model_route_data)
        selected_model = requested_model or str(model_route_data.get("model") or model_route.profile.model)
        selected_options = self._merge_options(options or ollama_options)
        enable_thinking, selected_options = self._extract_think(selected_options)
        enable_thinking = enable_thinking and self._supports_thinking(selected_model)

        available_tools = self.tools.available_tools()
        planner_tools = [name for name in available_tools if name in TOOL_SCHEMAS]

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
                messages=chat_messages,
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
                messages=chat_messages,
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

        if not self._likely_needs_tools(tool_signal_text):
            result = self._answer_direct(
                text,
                model=selected_model,
                system_prompt=system_prompt,
                options=selected_options,
                response_format=response_format,
                model_route=model_route_data,
                think=enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
                messages=chat_messages,
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

        return self._run_tool_loop(
            text=text,
            confirm=confirm,
            selected_model=selected_model,
            system_prompt=system_prompt,
            selected_options=selected_options,
            response_format=response_format,
            model_route_data=model_route_data,
            show_tool_traces=show_tool_traces,
            enable_thinking=enable_thinking,
            ollama_timeout_seconds=ollama_timeout_seconds,
            tool_timeout_seconds=tool_timeout_seconds,
            chat_messages=chat_messages,
            planner_tools=planner_tools,
            max_tool_calls=max_tool_calls,
        )

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
        installed, error = list_ollama_models(self.config)
        saved_models = results.get("models", {})
        saved_names = saved_models if isinstance(saved_models, dict) else {}
        model_names = sorted(set(installed) | set(results.get("last_inventory", [])) | set(saved_names), key=str.lower)
        if not model_names and error:
            return [
                {
                    "model": None,
                    "category": "unavailable",
                    "job": "check Ollama connectivity or run tooling-showcase benchmark --list-models",
                    "summary": error,
                    "chat_capable": False,
                }
            ]
        return [
            {
                "model": model,
                "category": "unprofiled",
                "job": "run tooling-showcase benchmark to assign this model",
                "summary": "No local benchmark profile has been recorded yet.",
                "chat_capable": True,
            }
            for model in model_names
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
        messages: list[dict[str, str]] | None = None,
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
            messages=messages,
        )
        if response_format is None:
            result.message = self._normalize_answer_text(result.message)
        result.data = {
            **(result.data or {}),
            "model": model,
            "model_route": model_route,
        }
        return result

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
        messages: list[dict[str, str]] | None = None,
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
            messages=_replace_last_user_message(messages or [], prompt),
        )
        result.data = {
            **(result.data or {}),
            "model": model,
            "model_route": model_route,
            "tool_steps": len(tool_context),
        }
        return result

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
        messages: list[dict[str, str]] | None = None,
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
            "messages": messages,
        }
        accepted = {
            key: value
            for key, value in kwargs.items()
            if value is not None and (accepts_kwargs or key in params)
        }
        return self.ollama.ask(prompt, **accepted)

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
