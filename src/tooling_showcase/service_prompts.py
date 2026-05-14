from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from tooling_showcase.tool_protocol import TOOL_SCHEMAS, parse_model_json, tool_schema_text


def split_thinking_text(message: str) -> tuple[str, str]:
    text = message or ""
    for start_marker, end_marker in (
        ("<think>", "</think>"),
        ("<thinking>", "</thinking>"),
        ("Thinking...", "...done thinking."),
    ):
        if start_marker in text and end_marker in text:
            before, rest = text.split(start_marker, 1)
            thinking, after = rest.split(end_marker, 1)
            return thinking.strip(), (before + after).strip()
    return "", text.strip()


def normalize_chat_messages(messages: list[dict[str, Any]] | None, current_text: str) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for item in messages or []:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in {"user", "assistant", "system"}:
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        cleaned.append({"role": role, "content": content})
    if current_text and (not cleaned or cleaned[-1]["role"] != "user" or cleaned[-1]["content"].strip() != current_text.strip()):
        cleaned.append({"role": "user", "content": current_text.strip()})
    return cleaned


def conversation_history_text(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "No previous chat messages were provided."
    rendered = []
    for item in messages[-12:]:
        role = item.get("role", "user").title()
        content = str(item.get("content") or "").strip()
        if content:
            rendered.append(f"{role}: {content}")
    return "\n\n".join(rendered) or "No previous chat messages were provided."


def replace_last_user_message(messages: list[dict[str, str]], content: str) -> list[dict[str, str]]:
    if not messages:
        return [{"role": "user", "content": content}]
    replaced = [dict(item) for item in messages]
    for index in range(len(replaced) - 1, -1, -1):
        if replaced[index].get("role") == "user":
            replaced[index] = {"role": "user", "content": content}
            return replaced
    replaced.append({"role": "user", "content": content})
    return replaced


def has_contextual_reference(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in (" it", "that", "this", "them", "those", "these", "above", "previous", "earlier", "same", "again"))


class PromptFormattingMixin:
    def _build_tool_decision_prompt(
        self,
        *,
        user_text: str,
        available_tools: list[str],
        previous_tool_context: list[str],
        step_index: int,
        max_tool_calls: int,
        messages: list[dict[str, str]] | None = None,
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

Recent chat context:
{conversation_history_text(messages or [])}

Current user message:
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

    def _normalize_answer_text(self, message: str) -> str:
        try:
            payload = parse_model_json(message)
        except Exception:
            return self._strip_loop_end_marker(message)
        answer = payload.get("answer") or payload.get("message")
        if isinstance(answer, str) and answer.strip():
            return self._strip_loop_end_marker(answer)
        return self._strip_loop_end_marker(message)

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
        lowered = model.lower()
        return bool(re.search(r"\bqwen(?:2\.5|3(?:\.5)?)", lowered))

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

    def _build_tool_choice_prompt(self, user_text: str, *args, **kwargs) -> str:
        return self._build_tool_decision_prompt(
            user_text=user_text,
            available_tools=kwargs.get("available_tools", self.tools.available_tools()),
            previous_tool_context=kwargs.get("previous_tool_context", []),
            step_index=kwargs.get("step_index", 0),
            max_tool_calls=kwargs.get("max_tool_calls", 4),
            messages=kwargs.get("messages"),
        )
