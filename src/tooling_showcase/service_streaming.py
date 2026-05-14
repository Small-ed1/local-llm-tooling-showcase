from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterator

from tooling_showcase.models import ActionResult, ToolCall
from tooling_showcase.service_prompts import (
    replace_last_user_message,
    split_thinking_text,
)
from tooling_showcase.tool_protocol import compact_tool_result


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

        context = self._prepare_request_context(
            text,
            model=model,
            options=options,
            ollama_options=ollama_options,
            messages=messages,
        )
        tool_calls: list[ToolCall] = []
        tool_context: list[str] = []

        if allow_tools:
            direct = self.router.route(text)
            if direct.route == "tool" and direct.action in context.available_tools:
                if direct.action != "shell_command" or str((direct.arguments or {}).get("command", "")).strip().lower() not in {"command", "a command", "shell command", "a shell command"}:
                    yield from self._stream_tool_execution(direct.action, direct.arguments or {}, confirm=confirm, tool_timeout_seconds=tool_timeout_seconds, tool_calls=tool_calls, tool_context=tool_context)
                    result = ActionResult(
                        ok=tool_calls[-1].ok,
                        message=tool_calls[-1].summary,
                        data={"model": context.selected_model, "model_route": context.model_route_data, "router": {"route": direct.route, "reason": direct.reason, "action": direct.action}},
                        tool_calls=tool_calls,
                    )
                    self._log_chat(text=text, result=result, model=context.selected_model, model_route=context.model_route_data, tool_calls=tool_calls, mode="deterministic_tool_route")
                    yield self._stream_final(result)
                    return

        if allow_tools and not self.config.ollama.enabled:
            legacy = self._legacy_direct_tool_fallback(text, confirm=confirm, tool_timeout_seconds=tool_timeout_seconds)
            if legacy is not None:
                for call in legacy.tool_calls:
                    yield {"type": "tool_result", "tool_call": asdict(call), "tool_calls": [asdict(item) for item in legacy.tool_calls]}
                self._log_chat(text=text, result=legacy, model=context.selected_model, model_route=context.model_route_data, tool_calls=legacy.tool_calls, mode="legacy_direct_tool_fallback_no_ollama")
                yield self._stream_final(legacy)
                return
            result = ActionResult(False, "Local Ollama fallback is disabled.", data={"model": context.selected_model, "model_route": context.model_route_data})
            self.journal.append({"route": "llm_fallback", "request": text, "ok": result.ok, "message": result.message})
            yield self._stream_final(result)
            return

        if not allow_tools:
            result = yield from self._stream_answer_direct(
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
            self._log_chat(text=text, result=result, model=context.selected_model, model_route=context.model_route_data, tool_calls=[], mode="chat_no_tools")
            return

        contextual_calls = self.tools.maybe_contextual_tool_calls(text)
        if any(call.tool_name == "web_search" and call.ok for call in contextual_calls):
            tool_calls.extend(contextual_calls)
            tool_context.extend(compact_tool_result(call) for call in contextual_calls)
            yield {"type": "tool_calls", "tool_calls": [asdict(call) for call in tool_calls]}
            result = yield from self._stream_answer_with_context(
                user_text=text,
                tool_context=tool_context,
                model=context.selected_model,
                system_prompt=system_prompt,
                options=context.selected_options,
                response_format=response_format,
                model_route=context.model_route_data,
                show_tool_traces=show_tool_traces,
                think=context.enable_thinking,
                ollama_timeout_seconds=ollama_timeout_seconds,
                existing_tool_calls=tool_calls,
                messages=context.chat_messages,
            )
            self._log_chat(text=text, result=result, model=context.selected_model, model_route=context.model_route_data, tool_calls=tool_calls, mode="contextual_web_answer")
            return

        if not self._likely_needs_tools(context.tool_signal_text):
            result = yield from self._stream_answer_direct(
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
            self._log_chat(text=text, result=result, model=context.selected_model, model_route=context.model_route_data, tool_calls=[], mode="chat_direct_no_tool_signals")
            return

        yield from self._stream_tool_loop_events(
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

    def _stream_tool_loop_events(
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
    ) -> Iterator[dict]:
        for event in self._iter_tool_loop_events(
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
            emit_content_delta=True,
        ):
            event_type = event.get("type")
            if event_type == "tool_start":
                yield event
            elif event_type == "tool_result":
                tool_calls = event.get("tool_calls") or []
                yield {
                    "type": "tool_result",
                    "tool_call": asdict(event["tool_call"]),
                    "tool_calls": [asdict(call) for call in tool_calls],
                }
            elif event_type == "content_delta":
                yield event
            elif event_type == "final_result":
                yield self._stream_final(event["result"])

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
