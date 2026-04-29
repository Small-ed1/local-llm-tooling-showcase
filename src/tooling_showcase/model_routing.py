from __future__ import annotations

from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True, slots=True)
class ModelProfile:
    model: str
    category: str
    job: str
    summary: str
    chat_capable: bool = True


@dataclass(frozen=True, slots=True)
class ModelRoute:
    profile: ModelProfile
    reason: str
    matched_signals: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self.profile)
        payload.update(
            {
                "reason": self.reason,
                "matched_signals": list(self.matched_signals),
            }
        )
        return payload


MODEL_PROFILES: tuple[ModelProfile, ...] = (
    ModelProfile(
        model="qwen3:8b",
        category="general",
        job="default everyday assistant",
        summary="Best overall balance for normal daily requests.",
    ),
    ModelProfile(
        model="qwen3.5:9b",
        category="coding",
        job="coding and technical implementation",
        summary="Best coding model left in the local set.",
    ),
    ModelProfile(
        model="mistral-nemo:12b",
        category="linux",
        job="linux troubleshooting and sysadmin help",
        summary="Strong Linux and debugging profile with good speed.",
    ),
    ModelProfile(
        model="qwen2.5:14b-instruct",
        category="reasoning",
        job="deep research, document-heavy analysis, and serious assistant work",
        summary="Strong reasoning, long-context, and summary performance.",
    ),
    ModelProfile(
        model="llama3.2:latest",
        category="fast",
        job="fast general responses",
        summary="Fastest useful model left for quick replies.",
    ),
    ModelProfile(
        model="dolphin3:latest",
        category="summary",
        job="quick summaries and casual chat",
        summary="Best summary-focused fast model, with weaker reasoning control.",
    ),
    ModelProfile(
        model="phi4:14b",
        category="roleplay",
        job="companion-style and personality-heavy conversations",
        summary="Strongest tone, personality, and companion-style responses.",
    ),
    ModelProfile(
        model="qwen2.5vl:7b",
        category="vision",
        job="image and mixed vision-text workflows",
        summary="Use when screenshots, photos, or visual analysis matter.",
    ),
    ModelProfile(
        model="nomic-embed-text:latest",
        category="embedding",
        job="primary embedding generation for retrieval and RAG",
        summary="Embedding-only model, not for chat responses.",
        chat_capable=False,
    ),
    ModelProfile(
        model="embeddinggemma:latest",
        category="embedding",
        job="secondary embedding generation for retrieval experiments",
        summary="Embedding-only model, not for chat responses.",
        chat_capable=False,
    ),
)

_BY_CATEGORY = {profile.category: profile for profile in MODEL_PROFILES}
_DEFAULT_PROFILE = _BY_CATEGORY["general"]

_VISION_PATTERNS = (
    r"\b(image|photo|picture|screenshot|diagram|chart|graph|ocr|scan|visual|vision)\b",
)
_ROLEPLAY_PATTERNS = (
    r"\b(roleplay|pretend|character|persona|companion|romance|flirt|story|fiction|in character)\b",
)
_CODING_PATTERNS = (
    r"\b(code|coding|program|function|class|method|refactor|debug|bug|stack trace|exception|pytest|unit test|integration test|lint|format|compile|typescript|javascript|python|rust|golang|go|sql|regex|api)\b",
)
_LINUX_PATTERNS = (
    r"\b(linux|arch|ubuntu|debian|fedora|systemd|journalctl|bash|shell|ssh|docker|podman|kernel|grub|pacman|apt|dnf|fstab|mount|service file|sysadmin)\b",
)
_RESEARCH_PATTERNS = (
    r"\b(compare|comparison|tradeoff|trade-off|analyze|analysis|architecture|design|proposal|research|investigate|why|reasoning|document|pdf|spec|report|long context|evidence)\b",
)
_SUMMARY_PATTERNS = (
    r"\b(summary|summarize|summarise|tldr|tl;dr|recap|condense|short version|brief summary)\b",
)
_FAST_PATTERNS = (
    r"\b(quick|quickly|fast|faster|brief|briefly|one-liner|one line|short answer)\b",
)
_EMBEDDING_PATTERNS = (
    r"\b(embedding|embeddings|rag|semantic search|vector search|retrieve|retrieval)\b",
)


def model_profiles() -> list[dict[str, object]]:
    return [asdict(profile) for profile in MODEL_PROFILES]


def route_model(text: str) -> ModelRoute:
    lowered = text.lower()
    if _matches_any(lowered, _VISION_PATTERNS):
        return _route("vision", lowered, "Routed to the vision model for image-centric work.")
    if _matches_any(lowered, _ROLEPLAY_PATTERNS):
        return _route(
            "roleplay",
            lowered,
            "Routed to the personality-focused model for roleplay or companion-style requests.",
        )
    if _matches_any(lowered, _EMBEDDING_PATTERNS):
        return _route(
            "reasoning",
            lowered,
            "Embedding workflows rely on tool-side retrieval, so chat stays on the reasoning model.",
        )
    if _matches_any(lowered, _SUMMARY_PATTERNS):
        return _route(
            "summary",
            lowered,
            "Routed to the summary-focused model because the request asked for a condensed answer.",
        )

    scored_routes = [
        _scored_route("coding", lowered, _CODING_PATTERNS),
        _scored_route("linux", lowered, _LINUX_PATTERNS),
        _scored_route("reasoning", lowered, _RESEARCH_PATTERNS),
        _scored_route("fast", lowered, _FAST_PATTERNS),
    ]
    scored_routes = [item for item in scored_routes if item[0] > 0]
    if scored_routes:
        priority = {
            "coding": 5,
            "linux": 4,
            "reasoning": 3,
            "summary": 2,
            "fast": 1,
        }
        scored_routes.sort(key=lambda item: (-item[0], -priority[item[1]], item[1]))
        _, category, signals = scored_routes[0]
        profile = _BY_CATEGORY[category]
        if category == "fast":
            reason = "Routed to the fast general model because the request emphasized speed or brevity."
        elif category == "summary":
            reason = "Routed to the summary-focused model because the request asked for a condensed answer."
        elif category == "reasoning":
            reason = "Routed to the reasoning model for analysis, comparison, or document-heavy work."
        elif category == "linux":
            reason = "Routed to the Linux-focused model for troubleshooting and system tasks."
        else:
            reason = "Routed to the coding model for implementation, debugging, or technical code work."
        return ModelRoute(profile=profile, reason=reason, matched_signals=tuple(signals))

    return ModelRoute(
        profile=_DEFAULT_PROFILE,
        reason="Routed to the default general assistant for an everyday request.",
        matched_signals=(),
    )


def _route(category: str, text: str, reason: str) -> ModelRoute:
    profile = _BY_CATEGORY[category]
    signals = _matched_signals(text, _patterns_for_category(category))
    return ModelRoute(profile=profile, reason=reason, matched_signals=tuple(signals))


def _scored_route(category: str, text: str, patterns: tuple[str, ...]) -> tuple[int, str, list[str]]:
    signals = _matched_signals(text, patterns)
    return len(signals), category, signals


def _patterns_for_category(category: str) -> tuple[str, ...]:
    return {
        "coding": _CODING_PATTERNS,
        "linux": _LINUX_PATTERNS,
        "reasoning": _RESEARCH_PATTERNS,
        "summary": _SUMMARY_PATTERNS,
        "fast": _FAST_PATTERNS,
        "roleplay": _ROLEPLAY_PATTERNS,
        "vision": _VISION_PATTERNS,
    }.get(category, ())


def _matched_signals(text: str, patterns: tuple[str, ...]) -> list[str]:
    signals: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            token = match.group(0).strip()
            if token and token not in signals:
                signals.append(token)
    return signals


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)
