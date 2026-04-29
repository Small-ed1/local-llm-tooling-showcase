#!/usr/bin/env python3
"""Add library tools to tools.py"""

import re

with open("src/tooling_showcase/tools.py", "r") as f:
    content = f.read()

# 1. Add import after 'from tooling_showcase.journal import EventJournal'
old1 = "from tooling_showcase.journal import EventJournal\nfrom tooling_showcase.models import ToolCall"
new1 = "from tooling_showcase.journal import EventJournal\nfrom tooling_showcase.library_tools import LocalLibrary\nfrom tooling_showcase.models import ToolCall"
content = content.replace(old1, new1)

# 2. Add self.library after self._load_tool_stats() in __init__
old2 = """        self._tool_stats_path = self.state_root / "tool_stats.json"
        self._tool_stats: dict[str, dict[str, int]] = self._load_tool_stats()

    def _select_state_root"""

new2 = """        self._tool_stats_path = self.state_root / "tool_stats.json"
        self._tool_stats: dict[str, dict[str, int]] = self._load_tool_stats()
        self.library = LocalLibrary.from_env()

    def _select_state_root"""

content = content.replace(old2, new2)

# 3. Add library methods before _build_registry
old3 = """    def _build_registry(self) -> dict[str, Any]:
        return {"""

new3 = """    def library_info(self, arguments: dict | None = None, *, confirm: bool = False):
        return ToolCall(
            tool_name="library_info",
            ok=True,
            summary=json.dumps(self.library.info(), indent=2),
            data=self.library.info(),
        )

    def library_search(self, arguments: dict | None = None, *, confirm: bool = False):
        arguments = arguments or {}
        query = str(arguments.get("query", "")).strip()
        limit = int(arguments.get("limit", 10))
        results = self.library.search(query, limit=limit)
        if not results:
            return ToolCall(
                tool_name="library_search",
                ok=True,
                summary=f"No library results found for: {query}",
                data={"results": []},
            )
        summary = "\\n\\n".join(
            f"{item['id']} | {item['title']} | {item['type']}\\n{item['path']}\\n{item.get('snippet', '')}"
            for item in results
        )
        return ToolCall(
            tool_name="library_search",
            ok=True,
            summary=summary,
            data={"results": results},
        )

    def library_read_epub(self, arguments: dict | None = None, *, confirm: bool = False):
        arguments = arguments or {}
        item_id = str(arguments.get("id", "")).strip()
        query = str(arguments.get("query", "")).strip()
        max_chars = int(arguments.get("max_chars", 12000))
        result = self.library.read_epub(item_id, query=query, max_chars=max_chars)
        return ToolCall(
            tool_name="library_read_epub",
            ok=bool(result.get("ok")),
            summary=result.get("text") or result.get("error", ""),
            data=result,
        )

    def _build_registry(self) -> dict[str, Any]:
        return {"""

content = content.replace(old3, new3)

# 4. Add to registry after latest_linux_kernel
old4 = '"latest_linux_kernel": self.latest_linux_kernel,'
new4 = '''"latest_linux_kernel": self.latest_linux_kernel,
            "library_info": self.library_info,
            "library_search": self.library_search,
            "library_read_epub": self.library_read_epub,'''
content = content.replace(old4, new4)

with open("src/tooling_showcase/tools.py", "w") as f:
    f.write(content)

print("Done")