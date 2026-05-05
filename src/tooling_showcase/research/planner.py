from __future__ import annotations

import re

from tooling_showcase.research.schemas import ResearchSession


class ResearchPlanner:
    def plan(self, goal: str, *, mode: str, depth: int) -> list[str]:
        plan = [
            "Clarify the research question and keep this workflow separate from normal chat.",
            "Inspect local project structure and core documentation.",
            "Gather citable local sources with read, search, index, and library tools.",
            "Extract source-backed claims and note limits.",
            "Write a Markdown report with sources, claims, and next steps.",
        ]
        if depth >= 3:
            plan.insert(3, "Search implementation-specific symbols, routes, and tests.")
        if mode == "hybrid":
            plan.insert(-1, "Use public web search after local evidence is collected.")
        return plan

    def tool_plan(self, session: ResearchSession) -> list[tuple[str, dict, str]]:
        terms = self.keywords(session.goal)
        calls: list[tuple[str, dict, str]] = [
            ("tree_view", {"path": ".", "max_depth": 3}, "Workspace tree"),
            ("read_file", {"path_text": "README.md"}, "README"),
            ("read_file", {"path_text": "pyproject.toml"}, "Project metadata"),
            ("content_search", {"query": "TOOL_SCHEMAS"}, "Tool protocol search"),
            ("content_search", {"query": "def run_server"}, "Server route search"),
        ]

        if session.depth >= 2:
            calls.append(("build_index", {}, "Local index build"))
            calls.append(("query_index", {"query": session.goal}, "Local index query"))

        for term in terms[: max(2, session.depth + 1)]:
            calls.append(("content_search", {"query": term}, f"Content search: {term}"))

        if session.mode == "hybrid":
            calls.append(("web_search", {"query": session.goal}, "Public web search"))

        return calls[: 6 + session.depth * 4]

    def keywords(self, text: str) -> list[str]:
        stop = {
            "the", "and", "for", "with", "this", "that", "from", "into", "your",
            "project", "local", "llm", "tooling", "showcase", "please", "create",
        }
        words = [w.lower() for w in re.findall(r"[a-zA-Z_][a-zA-Z0-9_'-]{2,}", text)]
        seen = []
        for word in words:
            if word not in stop and word not in seen:
                seen.append(word)
        defaults = ["research", "router", "tool", "index", "journal", "server"]
        return (seen + [item for item in defaults if item not in seen])[:8]
