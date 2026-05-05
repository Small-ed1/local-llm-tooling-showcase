from __future__ import annotations

from tooling_showcase.research.extractor import ResearchExtractor
from tooling_showcase.research.planner import ResearchPlanner
from tooling_showcase.research.report_writer import ResearchReportWriter
from tooling_showcase.research.schemas import ResearchSession, utc_now
from tooling_showcase.research.source_manager import ResearchSourceManager
from tooling_showcase.research.storage import ResearchStorage
from tooling_showcase.research.verifier import ResearchVerifier


class ResearchRunner:
    def __init__(self, storage: ResearchStorage, planner: ResearchPlanner, sources: ResearchSourceManager) -> None:
        self.storage = storage
        self.planner = planner
        self.sources = sources
        self.extractor = ResearchExtractor()
        self.verifier = ResearchVerifier()
        self.report_writer = ResearchReportWriter()

    def run(self, session_id: str) -> dict:
        session = self.storage.get(session_id)
        if not session:
            raise FileNotFoundError(f"Research session not found: {session_id}")

        session.status = "running"
        session.updated_at = utc_now()
        self.storage.save(session)

        try:
            session.sources = self.sources.gather(self.planner.tool_plan(session))
            session.findings = self.extractor.findings(session)
            session.claims = self.extractor.claims(session)
            notes = self.verifier.verify(session)
            session.report = self.report_writer.write(session, verification_notes=notes)
            session.status = "complete"
        except Exception as exc:
            session.status = "failed"
            session.errors.append(str(exc))

        session.updated_at = utc_now()
        return self.storage.save(session)
