from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RouteDecision:
    route: str
    reason: str
    action: str | None = None
    arguments: dict[str, Any] | None = None


@dataclass(slots=True)
class ToolCall:
    tool_name: str
    ok: bool
    summary: str
    data: dict[str, Any] | None = None


@dataclass(slots=True)
class ActionResult:
    ok: bool
    message: str
    data: dict[str, Any] | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass(slots=True)
class AdapterCard:
    adapter_id: str
    name: str
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
