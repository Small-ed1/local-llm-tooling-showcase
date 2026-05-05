from __future__ import annotations

from tooling_showcase.research.schemas import ResearchSession


class ResearchExtractor:
    def findings(self, session: ResearchSession) -> list[str]:
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

    def claims(self, session: ResearchSession) -> list[str]:
        return [finding for finding in self.findings(session) if "failed" not in finding.lower()]
