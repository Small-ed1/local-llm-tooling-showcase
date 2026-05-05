from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import uuid
from typing import Any

from tooling_showcase.models import ToolCall


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


@dataclass(slots=True)
class ResearchSession:
    id: str
    goal: str
    mode: str = "local"
    depth: int = 2
    status: str = "created"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    plan: list[str] = field(default_factory=list)
    sources: list[ResearchSource] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    report: str = ""
    errors: list[str] = field(default_factory=list)


class ResearchLab:
    """Small sidecar research runner.

    This intentionally reuses the existing ToolRuntime instead of changing the chat
    router or service flow. It is deterministic enough to work without Ollama.
    """

    def __init__(self, service) -> None:
        self.service = service
        self.root = service.config.project_root / "state" / "research"
        self.sessions_dir = self.root / "sessions"
        self.reports_dir = self.root / "reports"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def list_sessions(self) -> list[dict]:
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            sessions.append(self._summary(payload))
        return sessions

    def get(self, session_id: str) -> dict | None:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def start(self, goal: str, *, mode: str = "local", depth: int = 2) -> dict:
        goal = " ".join(str(goal or "").split())
        if not goal:
            raise ValueError("Research goal is required.")
        session = ResearchSession(
            id=f"research_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            goal=goal,
            mode=mode if mode in {"local", "hybrid"} else "local",
            depth=max(1, min(int(depth or 2), 4)),
            status="planned",
        )
        session.plan = self._plan(goal, mode=session.mode, depth=session.depth)
        payload = self._session_to_dict(session)
        self._save(payload)
        return payload

    def run(self, session_id: str) -> dict:
        payload = self.get(session_id)
        if not payload:
            raise FileNotFoundError(f"Research session not found: {session_id}")

        session = self._dict_to_session(payload)
        session.status = "running"
        session.updated_at = self._now()
        self._save(self._session_to_dict(session))

        try:
            for tool, args, title in self._tool_plan(session):
                call = self.service.tools.run_tool(tool, args, confirm=False)
                session.sources.append(self._source_from_call(call, title=title, query=json.dumps(args, sort_keys=True)))
            session.findings = self._extract_findings(session)
            session.report = self._write_report(session)
            session.status = "complete"
        except Exception as exc:  # keep prototype failures visible but contained
            session.status = "failed"
            session.errors.append(str(exc))

        session.updated_at = self._now()
        payload = self._session_to_dict(session)
        self._save(payload)
        if session.report:
            self._report_path(session.id).write_text(session.report, encoding="utf-8", newline="\n")
        return payload

    def delete(self, session_id: str) -> bool:
        deleted = False
        for path in (self._session_path(session_id), self._report_path(session_id)):
            if path.exists():
                path.unlink()
                deleted = True
        return deleted

    def _plan(self, goal: str, *, mode: str, depth: int) -> list[str]:
        plan = [
            "Clarify the research goal and treat this as a sidecar report, not normal chat behavior.",
            "Inspect local project structure and core documentation.",
            "Gather safe local sources using read/search/index tools.",
            "Extract direct findings from tool outputs.",
            "Write a Markdown report with sources, limitations, and next steps.",
        ]
        if depth >= 3:
            plan.insert(3, "Search for implementation-specific symbols and API routes.")
        if mode == "hybrid":
            plan.insert(-1, "Use public web search only after local sources are checked.")
        return plan

    def _tool_plan(self, session: ResearchSession) -> list[tuple[str, dict, str]]:
        terms = self._keywords(session.goal)
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

    def _keywords(self, text: str) -> list[str]:
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

    def _source_from_call(self, call: ToolCall, *, title: str, query: str) -> ResearchSource:
        data = call.data if isinstance(call.data, dict) else {}
        return ResearchSource(
            id=f"src_{uuid.uuid4().hex[:8]}",
            type=self._source_type(call.tool_name),
            title=title,
            tool=call.tool_name,
            query=query,
            ok=bool(call.ok),
            summary=str(call.summary or "")[:5000],
            data=data,
        )

    def _source_type(self, tool: str) -> str:
        if tool in {"web_search", "expand_search_result", "extract_webpage_content"}:
            return "web"
        if tool in {"query_index", "build_index", "list_indexed_sources"}:
            return "index"
        if tool.startswith("library_"):
            return "library"
        return "local"

    def _extract_findings(self, session: ResearchSession) -> list[str]:
        findings = []
        for source in session.sources:
            if not source.ok:
                findings.append(f"{source.title}: tool `{source.tool}` failed or returned no usable result.")
                continue
            first_line = next((line.strip() for line in source.summary.splitlines() if line.strip()), "")
            if not first_line:
                first_line = "Source returned structured data but little text."
            findings.append(f"{source.title}: {first_line[:280]}")
        return findings

    def _write_report(self, session: ResearchSession) -> str:
        source_lines = []
        for index, source in enumerate(session.sources, start=1):
            status = "ok" if source.ok else "failed"
            source_lines.append(
                f"{index}. **{source.title}** — `{source.tool}` / {source.type} / {status}\\n"
                f"   Query: `{source.query}`"
            )

        finding_lines = [f"- {finding}" for finding in session.findings] or ["- No findings extracted yet."]
        plan_lines = [f"- {step}" for step in session.plan]

        return f"""# Research Lab Report

## Goal

{session.goal}

## Mode

- Mode: `{session.mode}`
- Depth: `{session.depth}`
- Status: `{session.status}`
- Created: `{session.created_at}`
- Updated: `{self._now()}`

## Plan

{chr(10).join(plan_lines)}

## Findings

{chr(10).join(finding_lines)}

## Sources

{chr(10).join(source_lines)}

## Limitations

- This prototype is a sidecar research runner. It does not replace chat, routing, model selection, or normal tool-loop behavior.
- Findings are generated from safe tool outputs and simple extraction rules.
- The next version should add stronger claim objects, citation line ranges, contradiction checks, and an optional model critic pass.

## Next Implementation Steps

1. Add claim/evidence cards in the UI.
2. Add source expansion controls.
3. Add Markdown export download.
4. Add model-assisted synthesis when Ollama is available.
5. Add tests for local-only versus hybrid source rules.
"""

    def _summary(self, payload: dict) -> dict:
        return {
            "id": payload.get("id"),
            "goal": payload.get("goal"),
            "mode": payload.get("mode"),
            "depth": payload.get("depth"),
            "status": payload.get("status"),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "source_count": len(payload.get("sources") or []),
        }

    def _session_to_dict(self, session: ResearchSession) -> dict:
        payload = asdict(session)
        payload["sources"] = [asdict(source) if isinstance(source, ResearchSource) else source for source in session.sources]
        return payload

    def _dict_to_session(self, payload: dict) -> ResearchSession:
        sources = [
            ResearchSource(**source) if isinstance(source, dict) else source
            for source in payload.get("sources", [])
        ]
        return ResearchSession(
            id=payload["id"],
            goal=payload["goal"],
            mode=payload.get("mode", "local"),
            depth=int(payload.get("depth", 2)),
            status=payload.get("status", "created"),
            created_at=payload.get("created_at") or self._now(),
            updated_at=payload.get("updated_at") or self._now(),
            plan=list(payload.get("plan") or []),
            sources=sources,
            findings=list(payload.get("findings") or []),
            report=str(payload.get("report") or ""),
            errors=list(payload.get("errors") or []),
        )

    def _save(self, payload: dict) -> None:
        self._session_path(payload["id"]).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{self._safe_id(session_id)}.json"

    def _report_path(self, session_id: str) -> Path:
        return self.reports_dir / f"{self._safe_id(session_id)}.md"

    def _safe_id(self, session_id: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", session_id)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
