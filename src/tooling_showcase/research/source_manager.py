from __future__ import annotations

import json
import uuid

from tooling_showcase.models import ToolCall
from tooling_showcase.research.schemas import ResearchSource


class ResearchSourceManager:
    def __init__(self, tools) -> None:
        self.tools = tools

    def gather(self, calls: list[tuple[str, dict, str]]) -> list[ResearchSource]:
        sources = []
        for tool, args, title in calls:
            call = self.tools.run_tool(tool, args, confirm=False)
            sources.append(self.from_call(call, title=title, query=json.dumps(args, sort_keys=True)))
        return sources

    def from_call(self, call: ToolCall, *, title: str, query: str) -> ResearchSource:
        data = call.data if isinstance(call.data, dict) else {}
        return ResearchSource(
            id=f"src_{uuid.uuid4().hex[:8]}",
            type=self.source_type(call.tool_name),
            title=title,
            tool=call.tool_name,
            query=query,
            ok=bool(call.ok),
            summary=str(call.summary or "")[:5000],
            data=data,
        )

    def source_type(self, tool: str) -> str:
        if tool in {"web_search", "expand_search_result", "extract_webpage_content"}:
            return "web"
        if tool in {"query_index", "build_index", "list_indexed_sources"}:
            return "index"
        if tool.startswith("library_"):
            return "library"
        return "local"
