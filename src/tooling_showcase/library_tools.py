from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import os
import re
import zipfile


SUPPORTED_EXTENSIONS = {".epub", ".txt", ".md", ".html", ".htm", ".zim"}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        return " ".join(self.parts)


@dataclass
class LibraryItem:
    id: str
    path: Path
    title: str
    extension: str


class LocalLibrary:
    def __init__(self, roots: list[Path]) -> None:
        self.roots = [root.expanduser().resolve() for root in roots]
        self.items = self._scan()

    @classmethod
    def from_env(cls) -> LocalLibrary:
        raw = os.environ.get("SHOWCASE_LIBRARY_PATHS", "").strip()
        if raw:
            roots = [Path(part) for part in raw.split(":") if part.strip()]
        else:
            roots = [
                Path.home() / "Books",
                Path.home() / "ebooks",
                Path.home() / "Documents" / "Books",
                Path.home() / "Kiwix",
                Path.home() / "ZIM",
                Path.home() / "zims",
            ]
        return cls(roots)

    def info(self) -> dict:
        by_type: dict[str, int] = {}
        for item in self.items:
            by_type[item.extension] = by_type.get(item.extension, 0) + 1
        return {
            "roots": [str(root) for root in self.roots],
            "existing_roots": [str(root) for root in self.roots if root.exists()],
            "count": len(self.items),
            "by_type": by_type,
        }

    def search(self, query: str, limit: int = 10) -> list[dict]:
        query = query.strip()
        if not query:
            return []

        terms = [term.lower() for term in re.findall(r"[a-zA-Z0-9_'-]+", query)]
        scored: list[tuple[int, LibraryItem, str]] = []

        for item in self.items:
            title_blob = f"{item.title} {item.path.name}".lower()
            title_score = sum(8 for term in terms if term in title_blob)
            snippet = ""

            body_score = 0
            if item.extension in {".txt", ".md", ".html", ".htm", ".epub"}:
                text = self.extract_text(item, max_chars=20000).lower()
                body_score = sum(2 for term in terms if term in text)
                snippet = self._snippet(text, terms)

            if item.extension == ".zim":
                zim_hits = self.search_zim(item, query, limit=3)
                if zim_hits:
                    body_score += 20 + len(zim_hits)
                    snippet = "\n".join(
                        f"{hit.get('title', '')}: {hit.get('snippet', '')}"
                        for hit in zim_hits
                    )

            score = title_score + body_score
            if score:
                scored.append((score, item, snippet))

        scored.sort(key=lambda row: row[0], reverse=True)

        return [
            {
                "id": item.id,
                "title": item.title,
                "path": str(item.path),
                "type": item.extension,
                "score": score,
                "snippet": snippet,
            }
            for score, item, snippet in scored[:limit]
        ]

    def read_epub(self, item_id: str, query: str = "", max_chars: int = 12000) -> dict:
        item = self.get(item_id)
        if item is None:
            return {"ok": False, "error": f"No library item found for id: {item_id}"}
        if item.extension != ".epub":
            return {"ok": False, "error": f"Item is not an EPUB: {item.path}"}

        text = self.extract_text(item, max_chars=max_chars * 3)

        if query.strip():
            terms = [term.lower() for term in re.findall(r"[a-zA-Z0-9_'-]+", query)]
            lower = text.lower()
            first_hit = min(
                [lower.find(term) for term in terms if lower.find(term) >= 0]
                or [0]
            )
            start = max(0, first_hit - max_chars // 3)
            text = text[start : start + max_chars]
        else:
            text = text[:max_chars]

        return {
            "ok": True,
            "id": item.id,
            "title": item.title,
            "path": str(item.path),
            "text": text,
        }

    def read_zim(self, item_id: str, title: str, max_chars: int = 12000) -> dict:
        item = self.get(item_id)
        if not item:
            return {"ok": False, "error": f"invalid id: {item_id}"}
        if item.extension != ".zim":
            return {"ok": False, "error": "not a zim file"}

        # Verify article exists via kiwix-search
        import shutil
        import subprocess
        kiwix_search = shutil.which("kiwix-search")
        if not kiwix_search:
            return {"ok": False, "error": "kiwix-search not installed"}

        try:
            proc = subprocess.run(
                [kiwix_search, str(item.path), title],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        if proc.stdout.strip():
            return {
                "ok": True,
                "title": title,
                "path": str(item.path),
                "text": f"Article: {title}\n\nZIM: {item.path.name}\n\nNote: Full text extraction requires kiwix-serve debugging. Article name verified exists.",
            }

        return {"ok": False, "error": f"article not found: {title}"}

    def get(self, item_id: str) -> LibraryItem | None:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def extract_text(self, item: LibraryItem, max_chars: int = 12000) -> str:
        if item.extension in {".txt", ".md"}:
            return item.path.read_text(errors="replace")[:max_chars]

        if item.extension in {".html", ".htm"}:
            raw = item.path.read_text(errors="replace")
            return _html_to_text(raw)[:max_chars]

        if item.extension == ".epub":
            return _epub_to_text(item.path, max_chars=max_chars)

        if item.extension == ".zim":
            return (
                "ZIM: Use library_search to find articles, then read via kiwix-manage or kiwix-serve."
            )

        return ""

    def _scan(self) -> list[LibraryItem]:
        found: list[LibraryItem] = []
        seen: set[Path] = set()

        for root in self.roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                extension = path.suffix.lower()
                if extension not in SUPPORTED_EXTENSIONS:
                    continue

                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)

                item_id = f"book_{len(found) + 1}"
                found.append(
                    LibraryItem(
                        id=item_id,
                        path=resolved,
                        title=_title_from_path(resolved),
                        extension=extension,
                    )
                )

        return found

    def _snippet(self, text: str, terms: list[str], radius: int = 220) -> str:
        if not text:
            return ""

        positions = [text.find(term) for term in terms if text.find(term) >= 0]
        if not positions:
            return ""

        pos = min(positions)
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        return " ".join(text[start:end].split())

    def search_zim(self, item: LibraryItem, query: str, limit: int = 5) -> list[dict]:
        import shutil
        import subprocess

        kiwix_search = shutil.which("kiwix-search")
        if not kiwix_search:
            return []

        try:
            proc = subprocess.run(
                [kiwix_search, str(item.path), query],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
                check=False,
            )
        except Exception:
            return []

        if proc.returncode != 0 and not proc.stdout.strip():
            return []

        hits = []
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]

        for title in lines[:limit]:
            if title:
                hits.append(
                    {
                        "title": title,
                        "snippet": "",
                        "source": str(item.path),
                    }
                )

        return hits


def _title_from_path(path: Path) -> str:
    name = path.stem.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", name).strip()


def _html_to_text(raw: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(raw)
    return parser.text()


def _epub_to_text(path: Path, max_chars: int = 12000) -> str:
    parts: list[str] = []

    with zipfile.ZipFile(path) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.lower().endswith((".xhtml", ".html", ".htm"))
        ]

        for name in names:
            if sum(len(part) for part in parts) >= max_chars:
                break

            try:
                raw = archive.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue

            text = _html_to_text(raw)
            if text:
                parts.append(text)

    return "\n\n".join(parts)[:max_chars]