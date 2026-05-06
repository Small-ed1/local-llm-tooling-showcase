from __future__ import annotations

from tooling_showcase.research.extractor import ResearchExtractor
from tooling_showcase.research.modeler import ResearchModeler
from tooling_showcase.research.planner import ResearchPlanner
from tooling_showcase.research.report_writer import ResearchReportWriter
from tooling_showcase.research.schemas import ResearchSession, utc_now
from tooling_showcase.research.source_manager import ResearchSourceManager
from tooling_showcase.research.storage import ResearchStorage
from tooling_showcase.research.verifier import ResearchVerifier


class ResearchRunner:
    def __init__(self, storage: ResearchStorage, planner: ResearchPlanner, sources: ResearchSourceManager, modeler: ResearchModeler) -> None:
        self.storage = storage
        self.planner = planner
        self.sources = sources
        self.modeler = modeler
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
            tool_plan, source_trace = self.modeler.source_plan(session, fallback=self.planner.tool_plan(session))
            session.model_calls.append(source_trace)
            session.sources = self.sources.gather(tool_plan)
            session.findings = self.extractor.findings(session)
            session.claims = self.extractor.claims(session)
            model_claims, model_findings, extract_trace = self.modeler.extract(session)
            session.model_calls.append(extract_trace)
            if model_claims:
                session.claims = model_claims
            if model_findings:
                session.findings = model_findings
            notes = self.verifier.verify(session)
            model_report, report_trace = self.modeler.report(session, verification_notes=notes)
            session.model_calls.append(report_trace)
            session.status = "complete"
            if report_trace.get("ok") and self._usable_report(model_report):
                session.report = model_report
            else:
                session.report = self.report_writer.write(session, verification_notes=notes)
        except Exception as exc:
            session.status = "failed"
            session.errors.append(str(exc))

        session.updated_at = utc_now()
        return self.storage.save(session)

    def _usable_report(self, report: str) -> bool:
        text = str(report or "").strip().lower()
        if len(text) < 400:
            return False
        required = ("goal", "claims", "findings", "sources")
        return all(item in text for item in required)
