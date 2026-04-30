from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys


@dataclass(slots=True)
class OllamaConfig:
    enabled: bool = True
    endpoint: str = "http://127.0.0.1:11434/api/chat"
    model: str = "qwen3:8b"
    timeout_seconds: int = 120
    temperature: float = 0.2
    system_prompt: str = (
        "Background capability instructions: you have access to local files, code search, web lookup, shell, git, indexing, memory, and other tools. "
        "Preserve the active assistant persona from the client or conversation. Default to a vivid, expressive, engaging tone unless the user asks for something restrained. "
        "Use tool results when they help, but keep tool orchestration in the background. "
        "If no tool actually ran, do not claim that it did. Do not present yourself as a package, wrapper, or runtime unless the user explicitly asks."
    )


@dataclass(slots=True)
class ShellPolicy:
    require_confirmation_for_risky: bool = True
    timeout_seconds: int = 30
    max_output_chars: int = 12000
    blocked_substrings: tuple[str, ...] = (
        "sudo ",
        "rm -rf /",
        "mkfs",
        "dd if=",
        "shutdown",
        "reboot",
        "> /dev/sd",
        "chmod -R 777 /",
    )
    risky_substrings: tuple[str, ...] = (
        " rm ",
        " mv ",
        " cp ",
        " > ",
        " >> ",
        " git clean ",
        " git reset ",
        " pkill ",
        " kill ",
    )


@dataclass(slots=True)
class ShowcaseConfig:
    project_root: Path
    workspace_root: Path
    portfolio_root: Path
    journal_path: Path
    ollama: OllamaConfig
    shell_policy: ShellPolicy
    benchmark_path: Path | None = None


def load_config(project_root: Path | None = None) -> ShowcaseConfig:
    root = (project_root or Path.cwd()).resolve()
    workspace_root = Path(os.getenv("TOOLING_SHOWCASE_WORKSPACE", str(root))).resolve()
    portfolio_root = Path(
        os.getenv("TOOLING_SHOWCASE_PORTFOLIO", str(root.parent))
    ).resolve()
    journal_path = Path(
        os.getenv(
            "TOOLING_SHOWCASE_JOURNAL",
            str(root / "state" / "events.jsonl"),
        )
    ).resolve()
    benchmark_path = Path(
        os.getenv(
            "TOOLING_SHOWCASE_BENCHMARKS",
            str(root / "state" / "model_benchmarks.json"),
        )
    ).resolve()
    ollama = OllamaConfig(
        enabled=os.getenv("TOOLING_SHOWCASE_OLLAMA_ENABLED", "true").lower() != "false",
        endpoint=os.getenv(
            "TOOLING_SHOWCASE_OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/chat"
        ),
        model=os.getenv("TOOLING_SHOWCASE_OLLAMA_MODEL", "qwen3:8b"),
        timeout_seconds=int(os.getenv("TOOLING_SHOWCASE_OLLAMA_TIMEOUT", "120")),
        temperature=float(os.getenv("TOOLING_SHOWCASE_OLLAMA_TEMPERATURE", "0.2")),
    )
    shell_policy = ShellPolicy(
        timeout_seconds=int(os.getenv("TOOLING_SHOWCASE_TOOL_TIMEOUT", "30")),
    )
    return ShowcaseConfig(
        project_root=root,
        workspace_root=workspace_root,
        portfolio_root=portfolio_root,
        journal_path=journal_path,
        ollama=ollama,
        shell_policy=shell_policy,
        benchmark_path=benchmark_path,
    )


def default_project_root() -> Path:
    if len(sys.argv) > 0:
        return Path.cwd().resolve()
    return Path.cwd().resolve()
