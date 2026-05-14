from __future__ import annotations

import json
from importlib import resources


def load_tool_docs() -> dict[str, dict]:
    resource = resources.files("tooling_showcase").joinpath("static/tool_docs.json")
    try:
        payload = json.loads(resource.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Failed to load shared tool docs: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Shared tool docs must be a JSON object.")

    docs: dict[str, dict] = {}
    for tool_id, doc in payload.items():
        if not isinstance(tool_id, str) or not isinstance(doc, dict):
            raise RuntimeError("Shared tool docs must map tool ids to objects.")
        docs[tool_id] = dict(doc)
    return docs


TOOL_DOCS = load_tool_docs()


ADAPTER_USAGE = {
    "northstar": [
        "Use as a reference for deterministic command routing before LLM fallback.",
        "Compare its tool catalog style against this showcase's tool docs.",
        "Borrow voice-assistant style routing ideas when adding new commands.",
    ],
    "ars": [
        "Use as the heavier research-runtime reference.",
        "Inspect model-role mappings when expanding routing beyond chat models.",
        "Compare direct tool surfaces and retrieval/indexing structure.",
    ],
    "behavioral_os": [
        "Use as a clean service-boundary reference.",
        "Compare explicit route/action models against freeform chat glue.",
        "Borrow result-shape discipline for UI event rendering.",
    ],
    "mini_arena": [
        "Use as an event/state transition reference.",
        "Compare structured actions and immutable journaling patterns.",
        "Borrow pressure/resolver style event thinking when adding autonomous runs.",
    ],
}
