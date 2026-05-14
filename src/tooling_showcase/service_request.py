from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tooling_showcase.model_routing import route_model
from tooling_showcase.service_prompts import conversation_history_text, has_contextual_reference, normalize_chat_messages
from tooling_showcase.tool_protocol import TOOL_SCHEMAS


@dataclass
class RequestContext:
    text: str
    chat_messages: list[dict[str, str]]
    tool_signal_text: str
    model_route_data: dict[str, Any]
    selected_model: str
    selected_options: dict[str, Any]
    enable_thinking: bool
    available_tools: list[str]
    planner_tools: list[str]


class RequestPlanningMixin:
    def _prepare_request_context(
        self,
        text: str,
        *,
        model: str | None,
        options: dict[str, Any] | None,
        ollama_options: dict[str, Any] | None,
        messages: list[dict[str, Any]] | None,
    ) -> RequestContext:
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

        return RequestContext(
            text=text,
            chat_messages=chat_messages,
            tool_signal_text=tool_signal_text,
            model_route_data=model_route_data,
            selected_model=selected_model,
            selected_options=selected_options,
            enable_thinking=enable_thinking,
            available_tools=available_tools,
            planner_tools=planner_tools,
        )
