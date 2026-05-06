from __future__ import annotations

from pathlib import Path
import json
import re

from tooling_showcase.research.schemas import ResearchSession


class ResearchStorage:
    def __init__(self, root: Path) -> None:
        self.root = root
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
            sessions.append(self.summary(payload))
        return sessions

    def get(self, session_id: str) -> ResearchSession | None:
        path = self.session_path(session_id)
        if not path.exists():
            return None
        return ResearchSession.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save(self, session: ResearchSession) -> dict:
        payload = session.to_dict()
        self.session_path(session.id).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )
        if session.report:
            self.report_path(session.id).write_text(session.report, encoding="utf-8", newline="\n")
        elif self.report_path(session.id).exists():
            self.report_path(session.id).unlink()
        return payload

    def read_report(self, session_id: str) -> str:
        path = self.report_path(session_id)
        if path.exists():
            return path.read_text(encoding="utf-8")
        session = self.get(session_id)
        return session.report if session else ""

    def delete(self, session_id: str) -> bool:
        deleted = False
        for path in (self.session_path(session_id), self.report_path(session_id)):
            if path.exists():
                path.unlink()
                deleted = True
        return deleted

    def summary(self, payload: dict) -> dict:
        return {
            "id": payload.get("id"),
            "goal": payload.get("goal"),
            "mode": payload.get("mode"),
            "depth": payload.get("depth"),
            "status": payload.get("status"),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "source_count": len(payload.get("sources") or []),
            "claim_count": len(payload.get("claims") or []),
        }

    def session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{self.safe_id(session_id)}.json"

    def report_path(self, session_id: str) -> Path:
        return self.reports_dir / f"{self.safe_id(session_id)}.md"

    def safe_id(self, session_id: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", str(session_id or ""))
