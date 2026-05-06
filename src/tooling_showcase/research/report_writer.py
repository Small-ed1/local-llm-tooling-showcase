from __future__ import annotations

from tooling_showcase.research.schemas import ResearchSession, utc_now


class ResearchReportWriter:
    def write(self, session: ResearchSession, *, verification_notes: list[str] | None = None) -> str:
        source_lines = []
        for index, source in enumerate(session.sources, start=1):
            status = "ok" if source.ok else "failed"
            source_lines.append(
                f"{index}. **{source.title}** - `{source.tool}` / {source.type} / {status}\n"
                f"   Query: `{source.query}`"
            )

        finding_lines = [f"- {finding}" for finding in session.findings] or ["- No findings extracted yet."]
        claim_lines = [f"- {claim}" for claim in session.claims] or ["- No source-backed claims extracted yet."]
        plan_lines = [f"- {step}" for step in session.plan]
        verification_lines = [f"- {note}" for note in (verification_notes or [])] or ["- No verification warnings."]
        model_lines = [
            f"- {call.get('stage', 'model')} / {call.get('model', '') or 'unknown model'} / {'ok' if call.get('ok') else 'fallback'}: {call.get('summary', '')}"
            for call in session.model_calls
        ] or ["- No model calls recorded."]

        return f"""# Research Lab Report

## Goal

{session.goal}

## Mode

- Mode: `{session.mode}`
- Depth: `{session.depth}`
- Status: `{session.status}`
- Created: `{session.created_at}`
- Updated: `{utc_now()}`

## Plan

{chr(10).join(plan_lines)}

## Claims

{chr(10).join(claim_lines)}

## Findings

{chr(10).join(finding_lines)}

## Sources

{chr(10).join(source_lines)}

## Verification Notes

{chr(10).join(verification_lines)}

## Model Calls

{chr(10).join(model_lines)}

## Limitations

- Research Lab is a separate workflow. It does not replace chat, routing, model selection, or normal tool-loop behavior.
- Findings are generated from safe tool outputs and simple extraction rules.
- Model calls are best-effort and fall back to deterministic extraction/report writing when Ollama is disabled or unavailable.

## Next Steps

1. Expand or refine sources if the claim list is thin.
2. Review failed sources and rerun with a narrower question if needed.
3. Export this report when it is ready to keep outside local state.
"""
