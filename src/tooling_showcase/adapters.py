from __future__ import annotations

from pathlib import Path
import json
import re

from tooling_showcase.models import AdapterCard


class WorkspaceAdapters:
    def __init__(self, portfolio_root: Path) -> None:
        self.portfolio_root = portfolio_root

    def cards(self) -> list[AdapterCard]:
        return [
            self._northstar_card(),
            self._ars_card(),
            self._behavioral_os_card(),
            self._mini_arena_card(),
        ]

    def render_prompt_context(self) -> str:
        cards = [card for card in self.cards() if card.status == "available"]
        if not cards:
            return "No workspace adapters detected."
        lines: list[str] = []
        for card in cards:
            details = ", ".join(
                f"{key}={value}" for key, value in sorted(card.details.items())
            )
            suffix = f" Details: {details}" if details else ""
            lines.append(f"- {card.name}: {card.summary}{suffix}")
        return "\n".join(lines)

    def _northstar_card(self) -> AdapterCard:
        root = self.portfolio_root / "northstar"
        catalog_path = root / "prompts" / "tools" / "catalog.json"
        if not catalog_path.exists():
            return AdapterCard(
                "northstar", "Northstar", "missing", "Northstar repo not detected."
            )
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
        tool_count = len(payload.get("tools", []))
        return AdapterCard(
            "northstar",
            "Northstar",
            "available",
            "Voice-assistant style deterministic routing plus tool-aware LLM fallback.",
            {"tool_docs": tool_count, "path": str(root)},
        )

    def _ars_card(self) -> AdapterCard:
        root = self.portfolio_root / "autonomous-research-station"
        cli_path = root / "src" / "ars_station" / "cli.py"
        models_path = root / "models.yaml"
        if not cli_path.exists() or not models_path.exists():
            return AdapterCard(
                "ars",
                "Autonomous Research Station",
                "missing",
                "ARS repo not detected.",
            )
        tool_names = sorted(
            set(
                re.findall(
                    r'tool_name="([a-z_]+)"', cli_path.read_text(encoding="utf-8")
                )
            )
        )
        model_text = models_path.read_text(encoding="utf-8")
        roles = len(re.findall(r"^  [a-z_]+:", model_text, flags=re.M))
        return AdapterCard(
            "ars",
            "Autonomous Research Station",
            "available",
            "General local research runtime with direct tools, routing, and model roles.",
            {"direct_tools": len(tool_names), "roles": roles, "path": str(root)},
        )

    def _behavioral_os_card(self) -> AdapterCard:
        root = self.portfolio_root / "behavioral-os"
        service_path = root / "src" / "behavioral_os" / "assistant" / "service.py"
        if not service_path.exists():
            return AdapterCard(
                "behavioral_os",
                "Behavioral OS",
                "missing",
                "Behavioral OS repo not detected.",
            )
        text = service_path.read_text(encoding="utf-8")
        actions = len(re.findall(r'"[a-z_]+": lambda', text))
        return AdapterCard(
            "behavioral_os",
            "Behavioral OS",
            "available",
            "Clean assistant service boundary with explicit route and action models.",
            {"actions": actions, "path": str(root)},
        )

    def _mini_arena_card(self) -> AdapterCard:
        root = self.portfolio_root / "mini-arena-social-simulation"
        inference_path = root / "sim" / "inference.py"
        if not inference_path.exists():
            return AdapterCard(
                "mini_arena",
                "Mini Arena Social Simulation",
                "missing",
                "Mini Arena repo not detected.",
            )
        text = inference_path.read_text(encoding="utf-8")
        structured_actions = len(re.findall(r'type="[a-z_]+"', text))
        return AdapterCard(
            "mini_arena",
            "Mini Arena Social Simulation",
            "available",
            "Structured action generation and event-oriented state transitions.",
            {"structured_action_literals": structured_actions, "path": str(root)},
        )
