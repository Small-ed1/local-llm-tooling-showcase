from __future__ import annotations

import json
from typing import Any

from tooling_showcase.model_routing import route_model
from tooling_showcase.research.schemas import ResearchSession, utc_now


class ResearchModeler:
    def __init__(self, ollama) -> None:
        self.ollama = ollama
        self.timeout_seconds = min(int(getattr(ollama.config, "timeout_seconds", 30) or 30), 45)
        self.model = route_model("deep research analysis reasoning evidence report").profile.model

    def plan(self, goal: str, *, mode: str, depth: int, fallback: list[str]) -> tuple[list[str], dict[str, Any]]:
        prompt = (
            "Create a concise research plan for this local-first Research Lab workflow. "
            "Do not run tools. Return JSON only with a `steps` array of 4 to 7 concrete strings.\n\n"
            f"Goal: {goal}\nMode: {mode}\nDepth: {depth}"
        )
        result = self._ask_json("research.plan", prompt)
        steps = []
        if result["ok"]:
            payload = result.get("json") if isinstance(result.get("json"), dict) else {}
            steps = [str(item).strip() for item in payload.get("steps", []) if str(item).strip()]
        if not steps:
            steps = fallback
        return steps[:7], result

    def source_plan(self, session: ResearchSession, *, fallback: list[tuple[str, dict, str]]) -> tuple[list[tuple[str, dict, str]], dict[str, Any]]:
        prompt = (
            "Choose safe tool calls for a local-first Research Lab sidecar. "
            "The LLM is responsible for deciding which evidence to gather, but tools must stay read-only and bounded. "
            "Return JSON only with a `tools` array. Each item must have `tool`, `args`, and `title`. "
            "Allowed tools: tree_view, read_file, content_search, build_index, query_index, library_info, library_search"
            f"{', web_search' if session.mode == 'hybrid' else ''}. "
            "Prefer project/source files and index/search tools before broad searches. Do not include shell commands.\n\n"
            f"Goal: {session.goal}\nMode: {session.mode}\nDepth: {session.depth}\nPlan:\n"
            f"{chr(10).join(f'- {step}' for step in session.plan)}"
        )
        result = self._ask_json("research.source_plan", prompt)
        calls: list[tuple[str, dict, str]] = []
        if result["ok"]:
            payload = result.get("json") if isinstance(result.get("json"), dict) else {}
            calls = self._coerce_tool_plan(payload.get("tools"), mode=session.mode, limit=6 + session.depth * 4)
            if not calls:
                result["ok"] = False
                result["summary"] = "Model JSON did not include usable safe tool calls."
        return (calls or fallback)[: 6 + session.depth * 4], result

    def extract(self, session: ResearchSession) -> tuple[list[str], list[str], dict[str, Any]]:
        prompt = (
            "Extract source-backed claims and concise findings from these tool outputs. "
            "Return JSON only with `claims` and `findings` arrays. Keep every item grounded in the source summaries.\n\n"
            f"Goal: {session.goal}\nSources:\n{self._source_context(session)}"
        )
        result = self._ask_json("research.extract", prompt)
        claims: list[str] = []
        findings: list[str] = []
        if result["ok"]:
            payload = result.get("json") if isinstance(result.get("json"), dict) else {}
            claims = [str(item).strip() for item in payload.get("claims", []) if str(item).strip()]
            findings = [str(item).strip() for item in payload.get("findings", []) if str(item).strip()]
            if not claims and not findings:
                result["ok"] = False
                result["summary"] = "Model JSON did not include usable `claims` or `findings` arrays."
        return claims, findings, result

    def report(self, session: ResearchSession, *, verification_notes: list[str]) -> tuple[str, dict[str, Any]]:
        prompt = (
            "Write a Markdown research report grounded in the provided local tool outputs. "
            "Include Goal, Claims, Findings, Sources, Verification Notes, Limitations, and Next Steps. "
            "Do not invent sources.\n\n"
            f"Goal: {session.goal}\nMode: {session.mode}\nDepth: {session.depth}\n"
            f"Plan:\n{chr(10).join(f'- {step}' for step in session.plan)}\n\n"
            f"Claims:\n{chr(10).join(f'- {claim}' for claim in session.claims)}\n\n"
            f"Findings:\n{chr(10).join(f'- {finding}' for finding in session.findings)}\n\n"
            f"Verification Notes:\n{chr(10).join(f'- {note}' for note in verification_notes)}\n\n"
            f"Sources:\n{self._source_context(session)}"
        )
        result = self._ask_text("research.report", prompt)
        return (str(result.get("content") or "").strip(), result)

    def _coerce_tool_plan(self, items: Any, *, mode: str, limit: int) -> list[tuple[str, dict, str]]:
        allowed = {"tree_view", "read_file", "content_search", "build_index", "query_index", "library_info", "library_search"}
        if mode == "hybrid":
            allowed.add("web_search")
        calls: list[tuple[str, dict, str]] = []
        for item in (items if isinstance(items, list) else []):
            if not isinstance(item, dict):
                continue
            tool = str(item.get("tool") or "").strip()
            if tool not in allowed:
                continue
            args = item.get("args") if isinstance(item.get("args"), dict) else {}
            title = str(item.get("title") or tool.replace("_", " ")).strip()[:120]
            calls.append((tool, args, title or tool))
            if len(calls) >= limit:
                break
        return calls

    def _ask_json(self, stage: str, prompt: str) -> dict[str, Any]:
        trace = {"stage": stage, "ok": False, "at": utc_now(), "model": self.model}
        if not getattr(self.ollama.config, "enabled", False):
            trace["summary"] = "Ollama disabled; used deterministic fallback."
            return trace
        result = self.ollama.ask(
            prompt,
            model=self.model,
            system_prompt="You are a careful research planner. Return valid JSON exactly matching the requested shape.",
            response_format="json",
            options={"temperature": 0.2, "num_predict": 512},
            think=True,
            timeout_seconds=self.timeout_seconds,
        )
        trace["ok"] = bool(result.ok)
        trace["model"] = self.model
        trace["summary"] = result.message[:500]
        if result.data and result.data.get("thinking"):
            trace["thinking"] = str(result.data.get("thinking"))[:2000]
        if result.ok:
            try:
                trace["json"] = json.loads(result.message)
            except json.JSONDecodeError:
                trace["ok"] = False
                trace["summary"] = f"Model returned invalid JSON: {result.message[:300]}"
        return trace

    def _ask_text(self, stage: str, prompt: str) -> dict[str, Any]:
        trace = {"stage": stage, "ok": False, "at": utc_now(), "model": self.model}
        if not getattr(self.ollama.config, "enabled", False):
            trace["summary"] = "Ollama disabled; used deterministic fallback."
            return trace
        result = self.ollama.ask(
            prompt,
            model=self.model,
            system_prompt="You are a careful research writer. Stay grounded in the supplied tool outputs.",
            options={"temperature": 0.25, "num_predict": 512},
            think=True,
            timeout_seconds=self.timeout_seconds,
        )
        trace["ok"] = bool(result.ok)
        trace["model"] = self.model
        trace["summary"] = result.message[:500]
        if result.data and result.data.get("thinking"):
            trace["thinking"] = str(result.data.get("thinking"))[:2000]
        if result.ok:
            trace["content"] = result.message
        return trace

    def _source_context(self, session: ResearchSession) -> str:
        lines = []
        for index, source in enumerate(session.sources, start=1):
            lines.append(
                f"[{index}] {source.title} | tool={source.tool} | type={source.type} | ok={source.ok}\n"
                f"Query: {source.query}\nSummary: {source.summary[:1200]}"
            )
        return "\n\n".join(lines) or "No sources collected yet."
