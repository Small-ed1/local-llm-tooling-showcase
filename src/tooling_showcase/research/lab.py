from __future__ import annotations

from datetime import datetime, timezone
import uuid

from tooling_showcase.research.planner import ResearchPlanner
from tooling_showcase.research.modeler import ResearchModeler
from tooling_showcase.research.runner import ResearchRunner
from tooling_showcase.research.schemas import ResearchSession, utc_now
from tooling_showcase.research.source_manager import ResearchSourceManager
from tooling_showcase.research.storage import ResearchStorage


class ResearchLab:
    """Research workflow that borrows the app's existing tools."""

    def __init__(self, service) -> None:
        self.service = service
        self.storage = ResearchStorage(service.config.project_root / "state" / "research")
        self.planner = ResearchPlanner()
        self.modeler = ResearchModeler(service.ollama)
        self.runner = ResearchRunner(self.storage, self.planner, ResearchSourceManager(service.tools), self.modeler)

    def list_sessions(self) -> list[dict]:
        return self.storage.list_sessions()

    def get(self, session_id: str) -> dict | None:
        session = self.storage.get(session_id)
        return session.to_dict() if session else None

    def start(self, goal: str, *, mode: str = "local", depth: int = 2, model: str = "auto") -> dict:
        clean_goal = " ".join(str(goal or "").split())
        if not clean_goal:
            raise ValueError("Research goal is required.")
        clean_mode = mode if mode in {"local", "hybrid"} else "local"
        clean_depth = max(1, min(int(depth or 2), 4))
        clean_model = str(model or "auto").strip() or "auto"
        session = ResearchSession(
            id=f"research_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            goal=clean_goal,
            mode=clean_mode,
            depth=clean_depth,
            model=clean_model,
            status="planned",
        )
        session.plan, trace = ResearchModeler(self.service.ollama, model=clean_model).plan(
            clean_goal,
            mode=session.mode,
            depth=session.depth,
            fallback=self.planner.plan(clean_goal, mode=session.mode, depth=session.depth),
        )
        session.model_calls.append(trace)
        return self.storage.save(session)

    def run(self, session_id: str) -> dict:
        session = self.storage.get(session_id)
        if not session:
            raise FileNotFoundError(f"Research session not found: {session_id}")
        return self.runner.run(session_id, model=session.model)

    def update(self, session_id: str, *, goal: str, mode: str = "local", depth: int = 2, model: str = "auto", plan: list[str] | None = None) -> dict:
        session = self.storage.get(session_id)
        if not session:
            raise FileNotFoundError(f"Research session not found: {session_id}")
        clean_goal = " ".join(str(goal or "").split())
        if not clean_goal:
            raise ValueError("Research goal is required.")
        session.goal = clean_goal
        session.mode = mode if mode in {"local", "hybrid"} else "local"
        session.depth = max(1, min(int(depth or 2), 4))
        session.model = str(model or "auto").strip() or "auto"
        session.status = "planned"
        clean_plan = [" ".join(str(step or "").split()) for step in (plan or []) if " ".join(str(step or "").split())]
        if clean_plan:
            session.plan = clean_plan[:7]
            trace = {
                "stage": "research.plan",
                "ok": True,
                "at": utc_now(),
                "model": session.model,
                "summary": f"Plan edited locally with {len(session.plan)} steps.",
                "json": {"steps": session.plan},
            }
        else:
            session.plan, trace = ResearchModeler(self.service.ollama, model=session.model).plan(
                session.goal,
                mode=session.mode,
                depth=session.depth,
                fallback=self.planner.plan(session.goal, mode=session.mode, depth=session.depth),
            )
        session.sources = []
        session.claims = []
        session.findings = []
        session.report = ""
        session.errors = []
        session.model_calls.append(trace)
        session.updated_at = utc_now()
        return self.storage.save(session)

    def stop(self, session_id: str) -> dict:
        session = self.storage.get(session_id)
        if not session:
            raise FileNotFoundError(f"Research session not found: {session_id}")
        if session.status == "running":
            session.status = "stopped"
            session.updated_at = utc_now()
        return self.storage.save(session)

    def report(self, session_id: str) -> str:
        return self.storage.read_report(session_id)

    def export(self, session_id: str) -> dict:
        session = self.storage.get(session_id)
        if not session:
            raise FileNotFoundError(f"Research session not found: {session_id}")
        report = self.storage.read_report(session_id) or session.report
        filename = f"{self.storage.safe_id(session.goal)[:48] or session.id}.md"
        return {"id": session.id, "filename": filename, "content": report}

    def delete(self, session_id: str) -> bool:
        return self.storage.delete(session_id)
