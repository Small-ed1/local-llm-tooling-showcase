from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Iterator

from tooling_showcase.model_routing import route_model
from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.service_prompts import (
    conversation_history_text,
    has_contextual_reference,
    normalize_chat_messages,
    replace_last_user_message,
    split_thinking_text,
)
from tooling_showcase.tool_protocol import (
    TOOL_SCHEMAS,
    compact_tool_result,
    normalize_tool_arguments,
    parse_model_json,
)


class StreamingResponseMixin:
    def stream_handle(
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
        allow_tools: bool = True,
        max_tool_calls: int = 4,
        show_tool_traces: bool = False,
        ollama_timeout_seconds: int | None = None,
        tool_timeout_seconds: int | None = None,
    ) -> Iterator[dict]:
        text = text.strip()
        if not text:
            yield self._stream_final(ActionResult(False, "Empty message."))
            return

        chat_messages = normalize_chat_messages(messages, text)
        tool_signal_text = f"{conversation_history_text(chat_messages)}\n\nCurrent user message: {text}" if has_contextual_reference(text) else text

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
        tool_calls: list[ToolCall] = []
        tool_context: list[str] = []

        if allow_tools:
            direct = self.router.route(text)
            if direct.route == "tool" and direct.action in available_tools:
                if direct.action != "shell_command" or str((direct.arguments or {}).get("command", "")).strip().lower() not in {"command", "a command", "shell command", "a shell command"}:
                    yield from self._stream_tool_execution(direct.action, direct.arguments or {}, confirm=confirm, tool_timeout_seconds=tool_timeout_seconds, tool_calls=tool_calls, tool_context=tool_context)
                    result = ActionResult(
                        ok=tool_calls[-1].ok,
                        message=tool_calls[-1].summary,
                        data={"model": selected_model, "model_route": model_route_data, "router": {"route": direct.route, "reason": direct.reason, "action": direct.action}},
                        tool_calls=tool_calls,
                    )
                    self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=tool_calls, mode="deterministic_tool_route")
                    yield self._stream_final(result)
                    return

        if allow_tools and not self.config.ollama.enabled:
            legacy = self._legacy_direct_tool_fallback(text, confirm=confirm, tool_timeout_seconds=tool_timeout_seconds)
            if legacy is not None:
                for call in legacy.tool_calls:
                    yield {"type": "tool_result", "tool_call": asdict(call), "tool_calls": [asdict(item) for item in legacy.tool_calls]}
                self._log_chat(text=text, result=legacy, model=selected_model, model_route=model_route_data, tool_calls=legacy.tool_calls, mode="legacy_direct_tool_fallback_no_ollama")
                yield self._stream_final(legacy)
                return
            result = ActionResult(False, "Local Ollama fallback is disabled.", data={"model": selected_model, "model_route": model_route_data})
            self.journal.append({"route": "llm_fallback", "request": text, "ok": result.ok, "message": result.message})
            yield self._stream_final(result)
            return

        if not allow_tools:
            result = yield from self._stream_answer_direct(
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
            self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=[], mode="chat_no_tools")
            return

        contextual_calls = self.tools.maybe_contextual_tool_calls(text)
        if any(call.tool_name == "web_search" and call.ok for call in contextual_calls):
            tool_calls.extend(contextual_calls)
            tool_context.extend(compact_tool_result(call) for call in contextual_calls)
            yield {"type": "tool_calls", "tool_calls": [asdict(call) for call in tool_calls]}
            result = yield from self._stream_answer_with_context(
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
                existing_tool_calls=tool_calls,
                messages=chat_messages,
            )
            self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=tool_calls, mode="contextual_web_answer")
            return

        if not self._likely_needs_tools(tool_signal_text):
            result = yield from self._stream_answer_direct(
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
            self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=[], mode="chat_direct_no_tool_signals")
            return

        executed_signatures: set[tuple[str, str]] = set()
        for step_index in range(max_tool_calls):
            decision_result = self._ask_ollama(
                self._build_tool_decision_prompt(user_text=text, available_tools=planner_tools, previous_tool_context=tool_context, step_index=step_index, max_tool_calls=max_tool_calls, messages=chat_messages),
                model=selected_model,
                system_prompt=self._tool_decision_system_prompt(system_prompt),
                response_format="json",
                options=selected_options,
                think=False,
                stream=False,
                timeout_seconds=ollama_timeout_seconds,
            )
            if not decision_result.ok:
                result = ActionResult(False, f"Tool decision model call failed: {decision_result.message}", data={"model": selected_model, "model_route": model_route_data}, tool_calls=tool_calls)
                self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=tool_calls, mode="tool_decision_failed")
                yield self._stream_final(result)
                return
            try:
                decision = parse_model_json(decision_result.message)
            except Exception as exc:
                result = yield from self._stream_answer_with_context(
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
                    existing_tool_calls=tool_calls,
                    messages=chat_messages,
                )
                self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=tool_calls, mode="invalid_tool_json_recovered")
                return

            action = str(decision.get("action") or decision.get("type") or "").strip().lower()
            if action == "answer":
                answer_text = str(decision.get("answer") or decision.get("message") or "").strip()
                if decision.get("message") and "<END_OF_MESSAGE>" not in answer_text:
                    continue
                if answer_text and self._requires_tree_context(text) and not any(call.tool_name == "tree_view" for call in tool_calls):
                    yield from self._stream_tool_execution("tree_view", {"path": ".", "max_depth": 4}, confirm=confirm, tool_timeout_seconds=tool_timeout_seconds, tool_calls=tool_calls, tool_context=tool_context)
                    continue
                if answer_text and not enable_thinking and response_format is None:
                    answer_text = self._strip_loop_end_marker(answer_text)
                    yield {"type": "content_delta", "delta": answer_text}
                    result = ActionResult(True, answer_text, data={"model": selected_model, "model_route": model_route_data, "planner": decision}, tool_calls=tool_calls)
                    self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=tool_calls, mode="model_answered_without_more_tools")
                    yield self._stream_final(result)
                    return
                break

            if action != "tool_call":
                tool_context.append("Planner returned an unknown action. Valid actions are answer or tool_call.")
                continue
            tool_name = str(decision.get("tool_name", "")).strip()
            arguments = decision.get("arguments") or {}
            if not isinstance(arguments, dict):
                arguments = {}
            normalized_args = normalize_tool_arguments(tool_name, arguments)
            signature = (tool_name, json.dumps(normalized_args, sort_keys=True, default=str))
            if signature in executed_signatures:
                tool_context.append(f"Skipped duplicate tool call: {tool_name} {json.dumps(normalized_args, sort_keys=True, default=str)}")
                continue
            if tool_name not in planner_tools:
                bad_call = ToolCall(tool_name=tool_name or "unknown", ok=False, summary=f"Rejected model-requested tool. Tool is not available to the chat planner. Available planner tools: {', '.join(planner_tools)}", data={"requested_tool": tool_name, "available_tools": planner_tools})
                tool_calls.append(bad_call)
                tool_context.append(compact_tool_result(bad_call))
                yield {"type": "tool_result", "tool_call": asdict(bad_call), "tool_calls": [asdict(call) for call in tool_calls]}
                continue
            if not self._safe_auto_run(tool_name) and not confirm:
                blocked = ToolCall(tool_name=tool_name, ok=False, summary="Tool requires confirmation before running. Ask the user for confirmation or rerun with confirm=true.", data={"arguments": arguments, "requires_confirmation": True})
                tool_calls.append(blocked)
                tool_context.append(compact_tool_result(blocked))
                yield {"type": "tool_result", "tool_call": asdict(blocked), "tool_calls": [asdict(call) for call in tool_calls]}
                break
            yield from self._stream_tool_execution(tool_name, normalized_args, confirm=confirm, tool_timeout_seconds=tool_timeout_seconds, tool_calls=tool_calls, tool_context=tool_context)
            executed_signatures.add(signature)

        result = yield from self._stream_answer_with_context(
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
            existing_tool_calls=tool_calls,
            messages=chat_messages,
        )
        self._log_chat(text=text, result=result, model=selected_model, model_route=model_route_data, tool_calls=tool_calls, mode="model_tool_loop")

    def _stream_answer_direct(
        self,
        text: str,
        *,
        model: str,
        system_prompt: str | None,
        options: dict[str, Any],
        response_format: str | dict | None,
        model_route: dict[str, Any],
        think: bool,
        ollama_timeout_seconds: int | None,
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[dict]:
        result = yield from self._stream_ollama_answer(
            text,
            model=model,
            system_prompt=system_prompt,
            options=options,
            response_format=response_format,
            model_route=model_route,
            think=think,
            ollama_timeout_seconds=ollama_timeout_seconds,
            tool_calls=[],
            tool_steps=None,
            messages=messages,
        )
        if response_format is None:
            result.message = self._normalize_answer_text(result.message)
        yield self._stream_final(result)
        return result

    def _stream_answer_with_context(
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
        think: bool,
        ollama_timeout_seconds: int | None,
        recovery_note: str | None = None,
        existing_tool_calls: list[ToolCall] | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[dict]:
        prompt = self._build_final_prompt(
            user_text=user_text,
            tool_context=tool_context,
            show_tool_traces=show_tool_traces,
            recovery_note=recovery_note,
        )
        result = yield from self._stream_ollama_answer(
            prompt,
            model=model,
            system_prompt=system_prompt,
            options=options,
            response_format=response_format,
            model_route=model_route,
            think=think,
            ollama_timeout_seconds=ollama_timeout_seconds,
            tool_calls=existing_tool_calls or [],
            tool_steps=len(tool_context),
            messages=replace_last_user_message(messages or [], prompt),
        )
        yield self._stream_final(result)
        return result

    def _stream_ollama_answer(
        self,
        prompt: str,
        *,
        model: str,
        system_prompt: str | None,
        options: dict[str, Any],
        response_format: str | dict | None,
        model_route: dict[str, Any],
        think: bool,
        ollama_timeout_seconds: int | None,
        tool_calls: list[ToolCall],
        tool_steps: int | None,
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[dict]:
        content_parts: list[str] = []
        thinking_parts: list[str] = []
        raw_data: dict[str, Any] = {}
        if hasattr(self.ollama, "stream_events"):
            events = self.ollama.stream_events(
                prompt,
                model=model,
                system_prompt=system_prompt,
                response_format=response_format,
                options=options,
                think=think,
                timeout_seconds=ollama_timeout_seconds,
                messages=messages,
            )
        else:
            fallback = self._ask_ollama(
                prompt,
                model=model,
                system_prompt=system_prompt,
                response_format=response_format,
                options=options,
                think=think,
                stream=False,
                timeout_seconds=ollama_timeout_seconds,
                messages=messages,
            )
            events = iter([{"type": "content_delta", "delta": fallback.message}, {"type": "ollama_done", "data": fallback.data or {}}])

        for event in events:
            event_type = event.get("type")
            if event_type == "content_delta":
                delta = str(event.get("delta") or "")
                content_parts.append(delta)
                yield {"type": "content_delta", "delta": delta}
            elif event_type == "thinking_delta":
                delta = str(event.get("delta") or "")
                thinking_parts.append(delta)
                yield {"type": "thinking_delta", "delta": delta}
            elif event_type == "ollama_done":
                raw_data = event.get("data") if isinstance(event.get("data"), dict) else {}
            elif event_type == "error":
                message = str(event.get("message") or "Ollama request failed.")
                result = ActionResult(False, message, data={"model": model, "model_route": model_route}, tool_calls=list(tool_calls))
                return result

        message = "".join(content_parts).strip()
        thinking = "".join(thinking_parts).strip()
        if not message:
            result = ActionResult(False, "Ollama streaming returned empty.", data={"model": model, "model_route": model_route}, tool_calls=list(tool_calls))
            return result
        data = {**raw_data, "thinking": thinking, "model": model, "model_route": model_route}
        if tool_steps is not None:
            data["tool_steps"] = tool_steps
        return ActionResult(True, message, data=data, tool_calls=list(tool_calls))

    def _stream_tool_execution(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        *,
        confirm: bool,
        tool_timeout_seconds: int | None,
        tool_calls: list[ToolCall],
        tool_context: list[str],
    ) -> Iterator[dict]:
        yield {"type": "tool_start", "tool_name": tool_name, "arguments": arguments}
        call = self.tools.run_tool(tool_name, arguments, confirm=confirm, timeout_seconds=tool_timeout_seconds)
        tool_calls.append(call)
        tool_context.append(compact_tool_result(call))
        yield {"type": "tool_result", "tool_call": asdict(call), "tool_calls": [asdict(item) for item in tool_calls]}

    def _stream_final(self, result: ActionResult) -> dict:
        thinking, clean_msg = self._split_stream_thinking(result)
        rendered_tools = [asdict(call) for call in result.tool_calls]
        return {
            "type": "final",
            "ok": result.ok,
            "message": clean_msg,
            "thinking": thinking,
            "tool_calls": rendered_tools,
            "data": result.data or {},
            "done": True,
        }

    def _split_stream_thinking(self, result: ActionResult) -> tuple[str, str]:
        data_thinking = str((result.data or {}).get("thinking") or "").strip()
        split_thinking, clean_msg = split_thinking_text(result.message)
        return data_thinking or split_thinking, clean_msg
