from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import math
import re


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    document_id: str
    label: str
    start_line: int
    end_line: int
    text: str


def build_chunks(
    documents: dict[str, str], max_lines_per_chunk: int = 12
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document_id, text in documents.items():
        lines = text.splitlines()
        label = Path(document_id).name or document_id
        for start in range(0, len(lines), max_lines_per_chunk):
            batch = lines[start : start + max_lines_per_chunk]
            if not batch:
                continue
            start_line = start + 1
            end_line = start + len(batch)
            numbered = "\n".join(
                f"{line_no}: {line}"
                for line_no, line in enumerate(batch, start=start_line)
            )
            chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    label=label,
                    start_line=start_line,
                    end_line=end_line,
                    text=numbered,
                )
            )
    return chunks


def query_chunks(
    chunks: list[DocumentChunk], query: str, limit: int = 4
) -> list[DocumentChunk]:
    query_terms = _tokenize(query)
    if not query_terms:
        return chunks[:limit]
    scored: list[tuple[float, DocumentChunk]] = []
    query_term_set = set(query_terms)
    for chunk in chunks:
        terms = _tokenize(chunk.text)
        if not terms:
            continue
        score = _cosine_overlap(query_term_set, terms)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda item: (-item[0], item[1].label, item[1].start_line))
    return [chunk for _, chunk in scored[:limit]] or chunks[:limit]


def save_index(chunks: list[DocumentChunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(chunk) for chunk in chunks]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")


def load_index(path: Path) -> list[DocumentChunk]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [DocumentChunk(**row) for row in payload]


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9_\-]{3,}", text.lower())]


def _cosine_overlap(query_terms: set[str], terms: list[str]) -> float:
    term_counts: dict[str, int] = {}
    for term in terms:
        term_counts[term] = term_counts.get(term, 0) + 1
    dot = 0.0
    for term in query_terms:
        dot += float(term_counts.get(term, 0))
    if dot == 0:
        return 0.0
    query_norm = math.sqrt(float(len(query_terms)))
    doc_norm = math.sqrt(float(sum(count * count for count in term_counts.values())))
    if query_norm == 0 or doc_norm == 0:
        return 0.0
    return dot / (query_norm * doc_norm)
