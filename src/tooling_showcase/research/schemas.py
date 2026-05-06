from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ResearchSource:
    id: str
    type: str
    title: str
    tool: str
    query: str
    ok: bool
    summary: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResearchSession:
    id: str
    goal: str
    mode: str = "local"
    depth: int = 2
    status: str = "created"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    plan: list[str] = field(default_factory=list)
    sources: list[ResearchSource] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    report: str = ""
    errors: list[str] = field(default_factory=list)
    model_calls: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sources"] = [source.to_dict() if isinstance(source, ResearchSource) else source for source in self.sources]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ResearchSession":
        sources = [
            ResearchSource(**source) if isinstance(source, dict) else source
            for source in payload.get("sources", [])
        ]
        return cls(
            id=str(payload["id"]),
            goal=str(payload["goal"]),
            mode=str(payload.get("mode", "local")),
            depth=int(payload.get("depth", 2)),
            status=str(payload.get("status", "created")),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
            plan=list(payload.get("plan") or []),
            sources=sources,
            claims=list(payload.get("claims") or []),
            findings=list(payload.get("findings") or []),
            report=str(payload.get("report") or ""),
            errors=list(payload.get("errors") or []),
            model_calls=list(payload.get("model_calls") or []),
        )
