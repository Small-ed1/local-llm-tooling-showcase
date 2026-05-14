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

    def run(self, session_id: str, *, model: str | None = None) -> dict:
        session = self.storage.get(session_id)
        if not session:
            raise FileNotFoundError(f"Research session not found: {session_id}")

        run_model = model if model and model != "auto" else session.model
        modeler = ResearchModeler(self.modeler.ollama, model=run_model)
        cycles = max(2, min(int(session.depth or 2), 4))

        session.status = "running"
        session.updated_at = utc_now()
        self.storage.save(session)

        try:
            session.iterations = []
            all_sources = []
            all_claims = []
            all_findings = []
            all_notes = []

            for cycle in range(1, cycles + 1):
                session.plan = list(session.plan or self.planner.plan(session.goal, mode=session.mode, depth=session.depth))
                tool_plan, source_trace = modeler.source_plan(session, fallback=self.planner.tool_plan(session))
                source_trace["cycle"] = cycle
                session.model_calls.append(source_trace)

                cycle_sources = self.sources.gather(tool_plan)
                all_sources.extend(cycle_sources)
                session.sources = list(all_sources)

                session.findings = self.extractor.findings(session)
                session.claims = self.extractor.claims(session)
                model_claims, model_findings, extract_trace = modeler.extract(session)
                extract_trace["cycle"] = cycle
                session.model_calls.append(extract_trace)
                if model_claims:
                    all_claims.extend(model_claims)
                if model_findings:
                    all_findings.extend(model_findings)

                session.claims = self._unique_text(all_claims or session.claims)
                session.findings = self._unique_text(all_findings or session.findings)
                notes = self.verifier.verify(session)
                all_notes.extend(notes)

                session.iterations.append(
                    {
                        "cycle": cycle,
                        "plan": list(session.plan),
                        "source_count": len(cycle_sources),
                        "claim_count": len(session.claims),
                        "finding_count": len(session.findings),
                        "verification_notes": list(notes),
                    }
                )

                if cycle < cycles:
                    fallback = self._next_plan_fallback(session, notes, cycle=cycle, total_cycles=cycles)
                    session.plan, expand_trace = modeler.expand(session, verification_notes=notes, fallback=fallback)
                    expand_trace["cycle"] = cycle
                    session.model_calls.append(expand_trace)

            session.sources = all_sources
            session.claims = self._unique_text(all_claims or session.claims)
            session.findings = self._unique_text(all_findings or session.findings)
            notes = self.verifier.verify(session) + self._unique_text(all_notes)
            model_report, report_trace = modeler.report(session, verification_notes=notes)
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

    def _unique_text(self, items: list[str]) -> list[str]:
        seen = set()
        unique = []
        for item in items:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            unique.append(text)
        return unique

    def _next_plan_fallback(self, session: ResearchSession, notes: list[str], *, cycle: int, total_cycles: int) -> list[str]:
        base = list(session.plan or self.planner.plan(session.goal, mode=session.mode, depth=session.depth))
        additions = [
            f"Cycle {cycle + 1} of {total_cycles}: verify the weakest claim with more targeted evidence.",
            "Re-check the most important source summaries against the current plan.",
        ]
        if notes:
            additions.append(f"Address verification note: {notes[0]}")
        for step in additions:
            if step not in base:
                base.append(step)
        return base[:7]
