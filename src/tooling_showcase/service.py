from __future__ import annotations

from dataclasses import asdict
import inspect
import json
from typing import Any

from tooling_showcase.benchmarking import benchmark_profiles, default_benchmark_path, list_ollama_models, load_benchmark_results
from tooling_showcase.config import ShowcaseConfig
from tooling_showcase.journal import EventJournal
from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.ollama import OllamaClient
from tooling_showcase.router import IntentRouter
from tooling_showcase.service_fallbacks import DirectFallbackMixin
from tooling_showcase.service_planner import PlannerLoopMixin
from tooling_showcase.service_prompts import (
    PromptFormattingMixin,
    replace_last_user_message as _replace_last_user_message,
)
from tooling_showcase.service_request import RequestPlanningMixin
from tooling_showcase.service_streaming import StreamingResponseMixin
from tooling_showcase.tool_protocol import compact_tool_result, parse_model_json
from tooling_showcase.tools import ToolRuntime


class ShowcaseService(
    PromptFormattingMixin,
    RequestPlanningMixin,
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

        context = self._prepare_request_context(
            text,
            model=model,
            options=options,
            ollama_options=ollama_options,
            messages=messages,
        )

        if allow_tools:
            direct = self._deterministic_tool_route(
                text,
                confirm=confirm,
                model=context.selected_model,
                model_route=context.model_route_data,
                available_tools=context.available_tools,
                tool_timeout_seconds=tool_timeout_seconds,
            )
            if direct is not None:
                self._log_chat(
                    text=text,
                    result=direct,
                    model=context.selected_model,
                    model_route=context.model_route_data,
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
                    model=context.selected_model,
                    model_route=context.model_route_data,
                    tool_calls=legacy.tool_calls,
                    mode="legacy_direct_tool_fallback_no_ollama",
                )
                return legacy

            result = ActionResult(False, "Local Ollama fallback is disabled.")
            result.data = {
                "model": context.selected_model,
                "model_route": context.model_route_data,
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
                model=context.selected_model,
                system_prompt=system_prompt,
                options=context.selected_options,
                response_format=response_format,
                model_route=context.model_route_data,
                think=context.enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
                messages=context.chat_messages,
            )
            self._log_chat(
                text=text,
                result=result,
                model=context.selected_model,
                model_route=context.model_route_data,
                tool_calls=[],
                mode="chat_no_tools",
            )
            return result

        contextual_calls = self.tools.maybe_contextual_tool_calls(text)
        if any(call.tool_name == "web_search" and call.ok for call in contextual_calls):
            result = self._answer_with_context(
                user_text=text,
                tool_context=[compact_tool_result(call) for call in contextual_calls],
                model=context.selected_model,
                system_prompt=system_prompt,
                options=context.selected_options,
                response_format=response_format,
                model_route=context.model_route_data,
                show_tool_traces=show_tool_traces,
                think=context.enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
                messages=context.chat_messages,
            )
            result.tool_calls.extend(contextual_calls)
            self._log_chat(
                text=text,
                result=result,
                model=context.selected_model,
                model_route=context.model_route_data,
                tool_calls=contextual_calls,
                mode="contextual_web_answer",
            )
            return result

        if not self._likely_needs_tools(context.tool_signal_text):
            result = self._answer_direct(
                text,
                model=context.selected_model,
                system_prompt=system_prompt,
                options=context.selected_options,
                response_format=response_format,
                model_route=context.model_route_data,
                think=context.enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
                messages=context.chat_messages,
            )
            self._log_chat(
                text=text,
                result=result,
                model=context.selected_model,
                model_route=context.model_route_data,
                tool_calls=[],
                mode="chat_direct_no_tool_signals",
            )
            return result

        return self._run_tool_loop(
            text=text,
            confirm=confirm,
            selected_model=context.selected_model,
            system_prompt=system_prompt,
            selected_options=context.selected_options,
            response_format=response_format,
            model_route_data=context.model_route_data,
            show_tool_traces=show_tool_traces,
            enable_thinking=context.enable_thinking,
            ollama_timeout_seconds=ollama_timeout_seconds,
            tool_timeout_seconds=tool_timeout_seconds,
            chat_messages=context.chat_messages,
            planner_tools=context.planner_tools,
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
        model: str | None = None,
        system_prompt: str | None = None,
        options: dict[str, Any] | None = None,
        ollama_timeout_seconds: int | None = None,
        tool_timeout_seconds: int | None = None,
        max_tool_calls_per_step: int = 3,
    ) -> ActionResult:
        goal = str(goal or "").strip()
        if not goal:
            return ActionResult(False, "Autonomous goal is empty.")
        steps = self._plan_autonomous_steps(
            goal,
            max_steps=max_steps,
            model=model,
            system_prompt=system_prompt,
            options=options,
            ollama_timeout_seconds=ollama_timeout_seconds,
        )
        plan_result = self.tools.plan_task(goal, steps)
        if not plan_result.ok:
            return ActionResult(False, f"Failed to plan task: {plan_result.summary}", tool_calls=[plan_result])

        task_id = str((plan_result.data or {}).get("task_id", ""))
        calls = [plan_result]
        step_results: list[dict[str, Any]] = []
        for step_num, step_title in enumerate(steps):
            execute_result = self.tools.execute_step(task_id, step_num)
            calls.append(execute_result)
            if not execute_result.ok:
                break
            step_prompt = self._autonomous_step_prompt(goal, steps, step_num, step_results)
            step_result = self.handle(
                step_prompt,
                confirm=confirm,
                model=model,
                system_prompt=system_prompt,
                options=options,
                allow_tools=True,
                max_tool_calls=max_tool_calls_per_step,
                show_tool_traces=True,
                ollama_timeout_seconds=ollama_timeout_seconds,
                tool_timeout_seconds=tool_timeout_seconds,
            )
            calls.extend(step_result.tool_calls)
            step_results.append(
                {
                    "step": step_num + 1,
                    "title": step_title,
                    "ok": step_result.ok,
                    "message": step_result.message,
                    "tool_calls": [asdict(call) for call in step_result.tool_calls],
                }
            )
            calls.append(self.tools.task_checkpoint(task_id, f"Step {step_num + 1}: {step_result.message[:1000]}"))
            if not step_result.ok:
                calls.append(self.tools.mark_step_failed(task_id, step_num, step_result.message))
                break
            calls.append(self.tools.mark_step_complete(task_id, step_num))

        status_result = self.tools.get_task_status(task_id)
        calls.append(status_result)
        task_status = (status_result.data or {}).get("status")
        ok = bool(status_result.ok and task_status == "completed")
        summary_lines = [f"{item['step']}. {item['title']}: {'ok' if item['ok'] else 'failed'}" for item in step_results]
        result = ActionResult(
            ok,
            f"Autonomous run {'completed' if ok else 'stopped'}: {goal}\n" + "\n".join(summary_lines),
            data={
                "autonomous": True,
                "max_steps": max_steps,
                "task_id": task_id,
                "steps": steps,
                "step_results": step_results,
                "task_status": task_status,
                "model": model,
            },
            tool_calls=calls,
        )
        return result

    def _plan_autonomous_steps(
        self,
        goal: str,
        *,
        max_steps: int,
        model: str | None,
        system_prompt: str | None,
        options: dict[str, Any] | None,
        ollama_timeout_seconds: int | None,
    ) -> list[str]:
        max_steps = max(1, min(int(max_steps), 12))
        if self.config.ollama.enabled:
            prompt = f"""
Create an execution plan for an autonomous local assistant run.
Return JSON only: {{"steps": ["short imperative step", "..."]}}.
Use between 1 and {max_steps} concrete steps.
Each step must be directly executable by a chat assistant with local tools.

Goal:
{goal}
""".strip()
            result = self._ask_ollama(
                prompt,
                model=self._normalize_model_choice(model),
                system_prompt=system_prompt,
                response_format="json",
                options=self._merge_options(options),
                timeout_seconds=ollama_timeout_seconds,
            )
            if result.ok:
                try:
                    payload = parse_model_json(result.message)
                    raw_steps = payload.get("steps") if isinstance(payload, dict) else None
                    steps = [str(step).strip() for step in raw_steps or [] if str(step).strip()]
                    if steps:
                        return steps[:max_steps]
                except (TypeError, ValueError, json.JSONDecodeError):
                    pass
        return self._fallback_autonomous_steps(goal, max_steps=max_steps)

    def _fallback_autonomous_steps(self, goal: str, *, max_steps: int) -> list[str]:
        candidates = [
            f"Inspect local context relevant to: {goal}",
            "Use the most relevant tools to gather missing evidence.",
            "Apply the requested change or produce the requested result.",
            "Verify the result with focused checks.",
            "Summarize what changed and any remaining risk.",
        ]
        return candidates[: max(1, min(max_steps, len(candidates)))]

    def _autonomous_step_prompt(
        self,
        goal: str,
        steps: list[str],
        step_index: int,
        previous_results: list[dict[str, Any]],
    ) -> str:
        previous = "\n".join(
            f"- Step {item['step']} {item['title']}: {item['message'][:500]}"
            for item in previous_results
        ) or "No previous autonomous steps have run."
        plan = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(steps))
        return f"""
Autonomous goal:
{goal}

Plan:
{plan}

Previous step results:
{previous}

Current step {step_index + 1}:
{steps[step_index]}

Complete only the current step. Use tools when they are needed. End with a concise status for this step.
""".strip()
