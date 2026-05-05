from __future__ import annotations

from tooling_showcase.research.schemas import ResearchSession


class ResearchVerifier:
    def verify(self, session: ResearchSession) -> list[str]:
        notes = []
        if not session.sources:
            notes.append("No sources were collected.")
        if not any(source.ok for source in session.sources):
            notes.append("No successful sources were collected.")
        if session.mode == "hybrid" and not any(source.type == "web" for source in session.sources):
            notes.append("Hybrid mode was requested, but no web source was captured.")
        return notes
