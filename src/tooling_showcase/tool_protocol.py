from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import re
from typing import Any

from tooling_showcase.models import ToolCall

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "web_search": {
        "description": "Search the public web for current, external, or factual information. Use for latest/current versions, releases, prices, news, public documentation, or anything likely to change.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
            },
            "required": ["query"],
        },
        "safe_auto_run": True,
    },
    "expand_search_result": {
        "description": "Fetch and extract text from a URL returned by web_search. Use to read the actual page content when search results are not enough to answer the question. Especially useful for official sources like kernel.org, docs.python.org, GitHub releases, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch."},
                "query": {"type": "string", "description": "Optional specific term to extract around."},
            },
            "required": ["url"],
        },
        "safe_auto_run": True,
    },
    "file_search": {
        "description": "Find candidate files in the workspace by filename. Use before read_file when the user mentions a file but not an exact path.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filename or partial filename."},
            },
            "required": ["query"],
        },
        "safe_auto_run": True,
    },
    "read_file": {
        "description": "Read a supported text file in the workspace. Use only when a path or filename is known.",
        "parameters": {
            "type": "object",
            "properties": {
                "path_text": {"type": "string", "description": "Path or filename to read."},
            },
            "required": ["path_text"],
        },
        "safe_auto_run": True,
    },
    "content_search": {
        "description": "Search inside workspace text files for an exact phrase, symbol, function name, class name, or keyword.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text or symbol to search for."},
            },
            "required": ["query"],
        },
        "safe_auto_run": True,
    },
    "build_index": {
        "description": "Build or rebuild the lightweight local workspace index. Use when the model needs broad repo search or repeated retrieval.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "safe_auto_run": True,
    },
    "query_index": {
        "description": "Search the built local index for relevant workspace chunks. Use for repo-level questions after an index exists.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Semantic or keyword query."},
            },
            "required": ["query"],
        },
        "safe_auto_run": True,
    },
    "tree_view": {
        "description": "Show a shallow directory tree for a workspace path. Use to inspect project structure.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path, default is workspace root."},
                "max_depth": {"type": "integer", "description": "Maximum depth to display."},
            },
            "required": [],
        },
        "safe_auto_run": True,
    },
    "adapter_inventory": {
        "description": "Inspect which known workspace adapters/projects are detected.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "safe_auto_run": True,
    },
    "library_info": {
        "description": "Show local library configuration and available library sources.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "safe_auto_run": True,
    },
    "library_search": {
        "description": "Search the local library for books, documents, EPUBs, or ZIM entries.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Library search query."},
                "limit": {"type": "integer", "description": "Maximum result count."},
            },
            "required": ["query"],
        },
        "safe_auto_run": True,
    },
    "library_read_epub": {
        "description": "Read or search inside an EPUB from the local library by id.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Library item id."},
                "query": {"type": "string", "description": "Optional query inside the EPUB."},
                "max_chars": {"type": "integer", "description": "Maximum characters to return."},
            },
            "required": ["id"],
        },
        "safe_auto_run": True,
    },
    "library_read_zim": {
        "description": "Read a ZIM article by library item id and title.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Library item id."},
                "title": {"type": "string", "description": "Article title."},
            },
            "required": ["id", "title"],
        },
        "safe_auto_run": True,
    },
    "draft_system_prompt": {
        "description": "Draft a structured system prompt suggestion with title, short message, context, and full prompt. Use only when the user asks to create or refine reusable assistant behavior; the UI/user still chooses whether to save it.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Prompt title."},
                "short_message": {"type": "string", "description": "Short summary shown in prompt lists."},
                "context": {"type": "string", "description": "Reusable background context."},
                "goal": {"type": "string", "description": "What this system prompt should optimize for."},
            },
            "required": [],
        },
        "safe_auto_run": True,
    },
    "shell_command": {
        "description": "Run a guarded shell command in the workspace. Use only when the user explicitly asks to run a command or inspect local runtime state. Risky commands require confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run."},
            },
            "required": ["command"],
        },
        "safe_auto_run": False,
    },
}


def visible_tool_schemas(available_tools: list[str]) -> list[dict[str, Any]]:
    """Return schemas only for tools actually registered in ToolRuntime."""
    visible = []
    for name in available_tools:
        schema = TOOL_SCHEMAS.get(name)
        if not schema:
            continue
        visible.append(
            {
                "name": name,
                "description": schema["description"],
                "parameters": schema["parameters"],
                "safe_auto_run": bool(schema.get("safe_auto_run", False)),
            }
        )
    return visible


def tool_schema_text(available_tools: list[str]) -> str:
    return json.dumps(visible_tool_schemas(available_tools), indent=2, sort_keys=True)


def normalize_tool_arguments(tool_name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    """Accept model-friendly names and normalize to your current Python method names."""
    args = dict(arguments or {})
    if tool_name == "read_file" and "path" in args and "path_text" not in args:
        args["path_text"] = args.pop("path")
    if tool_name == "shell_command" and "cmd" in args and "command" not in args:
        args["command"] = args.pop("cmd")
    return args


def tool_call_to_dict(call: ToolCall) -> dict[str, Any]:
    if is_dataclass(call):
        return asdict(call)
    return {
        "tool_name": getattr(call, "tool_name", "unknown"),
        "ok": bool(getattr(call, "ok", False)),
        "summary": str(getattr(call, "summary", "")),
        "data": getattr(call, "data", None),
    }


def compact_tool_result(call: ToolCall, *, max_chars: int = 5000) -> str:
    payload = tool_call_to_dict(call)
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [tool result truncated]"
    return text


def parse_model_json(text: str) -> dict[str, Any]:
    """Be forgiving with local models: accept raw JSON or JSON inside fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if not match:
            raise
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("Model JSON response must be an object.")
    return payload
