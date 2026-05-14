from __future__ import annotations

import json
from typing import Any

from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.tool_protocol import compact_tool_result, normalize_tool_arguments, parse_model_json


class PlannerLoopMixin:
    def _run_tool_loop(
        self,
        *,
        text: str,
        confirm: bool,
        selected_model: str,
        system_prompt: str | None,
        selected_options: dict[str, Any],
        response_format: str | dict | None,
        model_route_data: dict[str, Any],
        show_tool_traces: bool,
        enable_thinking: bool,
        ollama_timeout_seconds: int | None,
        tool_timeout_seconds: int | None,
        chat_messages: list[dict[str, str]],
        planner_tools: list[str],
        max_tool_calls: int,
    ) -> ActionResult:
        tool_calls: list[ToolCall] = []
        tool_context: list[str] = []
        executed_signatures: set[tuple[str, str]] = set()

        for step_index in range(max_tool_calls):
            decision_result = self._ask_ollama(
                self._build_tool_decision_prompt(
                    user_text=text,
                    available_tools=planner_tools,
                    previous_tool_context=tool_context,
                    step_index=step_index,
                    max_tool_calls=max_tool_calls,
                    messages=chat_messages,
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
                    messages=chat_messages,
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
            messages=chat_messages,
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
