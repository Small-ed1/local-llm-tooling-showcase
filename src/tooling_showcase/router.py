from __future__ import annotations

import re

from tooling_showcase.models import RouteDecision


class IntentRouter:
    def route(self, text: str) -> RouteDecision:
        stripped = text.strip()
        lowered = stripped.lower()

        if lowered.startswith(("find file ", "search files ")):
            query = stripped.split(maxsplit=2)[-1]
            return RouteDecision(
                route="tool",
                reason="Matches filename search phrasing.",
                action="file_search",
                arguments={"query": query},
            )

        if lowered.startswith(("read file ", "inspect file ", "summarize file ")):
            path_text = stripped.split(maxsplit=2)[-1]
            return RouteDecision(
                route="tool",
                reason="Matches direct file read phrasing.",
                action="read_file",
                arguments={"path": path_text},
            )

        if lowered.startswith(("write file ", "create file ", "append file ")):
            return RouteDecision(
                route="llm_fallback",
                reason="Write-style requests need structured arguments; keep them in fallback unless called programmatically.",
            )

        if lowered.startswith(
            ("search content ", "grep ", "find text ", "find symbol ")
        ):
            query = stripped.split(maxsplit=2)[-1]
            action = (
                "find_symbol" if lowered.startswith("find symbol ") else "grep_search"
            )
            key = "name" if action == "find_symbol" else "query"
            return RouteDecision(
                route="tool",
                reason="Matches content search phrasing.",
                action=action,
                arguments={key: query},
            )

        if lowered.startswith(("build index", "index project", "index files")):
            return RouteDecision(
                route="tool",
                reason="Matches local indexing request.",
                action="build_index",
                arguments={},
            )

        if lowered.startswith(("query index ", "search index ")):
            query = stripped.split(maxsplit=2)[-1]
            return RouteDecision(
                route="tool",
                reason="Matches index query phrasing.",
                action="query_index",
                arguments={"query": query},
            )

        if lowered.startswith(("search web for ", "look up ", "search docs for ")):
            query = re.sub(
                r"^(search web for|look up|search docs for)\s+",
                "",
                stripped,
                flags=re.I,
            )
            return RouteDecision(
                route="tool",
                reason="Matches web search phrasing.",
                action="web_search",
                arguments={"query": query},
            )

        if re.search(r"\b(weather|forecast|temperature)\b", lowered) and re.search(
            r"\b(in|for|at|tomorrow|today|tonight)\b", lowered
        ):
            return RouteDecision(
                route="tool",
                reason="Matches weather lookup phrasing.",
                action="weather_lookup",
                arguments={"query": stripped},
            )

        if "linux kernel" in lowered and any(
            word in lowered for word in ("latest", "current", "stable")
        ):
            return RouteDecision(
                route="tool",
                reason="Matches current Linux kernel phrasing.",
                action="latest_linux_kernel",
                arguments={},
            )

        if lowered in {"run tests", "test project", "pytest"}:
            return RouteDecision(
                route="tool",
                reason="Matches test execution phrasing.",
                action="run_tests",
                arguments={},
            )

        if lowered in {"lint code", "run lint", "lint project"}:
            return RouteDecision(
                route="tool",
                reason="Matches lint phrasing.",
                action="lint_code",
                arguments={},
            )

        if lowered in {"format code", "format project"}:
            return RouteDecision(
                route="tool",
                reason="Matches format phrasing.",
                action="format_code",
                arguments={},
            )

        if lowered in {"build project", "build"}:
            return RouteDecision(
                route="tool",
                reason="Matches build phrasing.",
                action="build_project",
                arguments={},
            )

        if lowered in {"git status", "show git status"}:
            return RouteDecision(
                route="tool",
                reason="Matches git status phrasing.",
                action="git_status",
                arguments={},
            )

        if lowered in {"git diff", "show git diff"}:
            return RouteDecision(
                route="tool",
                reason="Matches git diff phrasing.",
                action="git_diff",
                arguments={},
            )

        if lowered in {"git log", "show git log"}:
            return RouteDecision(
                route="tool",
                reason="Matches git log phrasing.",
                action="git_log",
                arguments={},
            )

        if lowered in {"list directory", "list files"}:
            return RouteDecision(
                route="tool",
                reason="Matches directory listing phrasing.",
                action="list_directory",
                arguments={},
            )

        if lowered.startswith(
            (
                "look around this project",
                "look around this repo",
                "look around this codebase",
                "inspect this project",
                "inspect this repo",
                "inspect this codebase",
                "investigate this project",
                "investigate this repo",
                "investigate this codebase",
                "figure out this repo",
                "figure out this project",
                "figure out this codebase",
                "show project structure",
                "show me the project structure",
                "what files are here",
            )
        ):
            return RouteDecision(
                route="tool",
                reason="Matches broad project inspection phrasing.",
                action="tree_view",
                arguments={"path": ".", "max_depth": 3},
            )

        if lowered.startswith(
            (
                "look online and compare",
                "search online and compare",
                "compare this repo to",
                "compare this project to",
            )
        ):
            return RouteDecision(
                route="tool",
                reason="Matches web-assisted comparison phrasing.",
                action="web_search",
                arguments={"query": stripped},
            )

        if lowered in {"tree view", "show tree"}:
            return RouteDecision(
                route="tool",
                reason="Matches tree view phrasing.",
                action="tree_view",
                arguments={},
            )

        if lowered in {"system info", "show system info"}:
            return RouteDecision(
                route="tool",
                reason="Matches system info phrasing.",
                action="system_info",
                arguments={},
            )

        if lowered.startswith(("run ", "shell ")):
            command = stripped.split(maxsplit=1)[1]
            return RouteDecision(
                route="tool",
                reason="Explicit shell request.",
                action="shell_command",
                arguments={"command": command},
            )

        if lowered in {
            "show adapters",
            "list adapters",
            "showcase sources",
            "compare source projects",
        }:
            return RouteDecision(
                route="tool",
                reason="Matches adapter inventory request.",
                action="adapter_inventory",
                arguments={},
            )

        return RouteDecision(
            route="llm_fallback",
            reason="No deterministic tool route matched cleanly.",
        )
