"""Glossary service Phase 4.

Sumber kebenaran: config/terminology.csv (format Phase 1.6, diperluas).
Kolom wajib: term, italic, category, note.
Kolom opsional (Phase 4 extension): language, case_sensitive, priority.

Tidak ada network call. Tidak ada auto-download.
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..config import TERMINOLOGY_FILE, EXCEPTIONS_FILE


@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    italic: bool
    category: str
    note: str
    language: str
    case_sensitive: bool
    priority: int
    pattern: re.Pattern


@dataclass(frozen=True)
class GlossaryMatch:
    term: str
    matched_text: str
    char_start: int
    char_end: int
    entry: GlossaryEntry


@dataclass
class GlossaryStatus:
    loaded: bool
    entry_count: int
    exception_count: int
    error: Optional[str] = None


def _build_pattern(term: str, case_sensitive: bool) -> re.Pattern:
    """Bangun regex untuk 1 kata atau frasa multi-kata.

    - Boundary Unicode-aware: (?<!\\w) ... (?!\\w).
    - Multiword: internal whitespace fleksibel (\\s+).
    - Tidak match di dalam kata lain.
    """
    parts = term.split()
    core = r"\s+".join(re.escape(p) for p in parts)
    pattern = r"(?<!\w)" + core + r"(?!\w)"
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)


class GlossaryService:
    def __init__(
        self,
        terminology_path: Path,
        exceptions_path: Optional[Path] = None,
    ) -> None:
        self.terminology_path = Path(terminology_path)
        self.exceptions_path = (
            Path(exceptions_path) if exceptions_path else None
        )
        self.entries: List[GlossaryEntry] = []
        self.exceptions: set = set()
        self.status = GlossaryStatus(
            loaded=False, entry_count=0, exception_count=0,
        )

    def load(self) -> GlossaryStatus:
        try:
            self.entries = self._load_terminology()
            self.exceptions = self._load_exceptions()
            self.status = GlossaryStatus(
                loaded=True,
                entry_count=len(self.entries),
                exception_count=len(self.exceptions),
                error=None,
            )
        except Exception as exc:  # defensive
            self.status = GlossaryStatus(
                loaded=False, entry_count=0, exception_count=0,
                error=f"Gagal memuat glossary: {type(exc).__name__}",
            )
        return self.status

    def _load_terminology(self) -> List[GlossaryEntry]:
        if not self.terminology_path.exists():
            return []
        entries: List[GlossaryEntry] = []
        with self.terminology_path.open(
            "r", encoding="utf-8", newline=""
        ) as f:
            reader = csv.DictReader(f)
            for row in reader:
                term = (row.get("term") or "").strip()
                if not term:
                    continue
                italic_raw = (row.get("italic") or "").strip().lower()
                italic = italic_raw in ("true", "1", "yes", "y")
                category = (row.get("category") or "").strip()
                note = (row.get("note") or "").strip()
                language = (row.get("language") or "").strip()
                cs_raw = (row.get("case_sensitive") or "").strip().lower()
                case_sensitive = cs_raw in ("true", "1", "yes", "y")
                prio_raw = (row.get("priority") or "0").strip()
                try:
                    priority = int(prio_raw) if prio_raw else 0
                except ValueError:
                    priority = 0
                entries.append(
                    GlossaryEntry(
                        term=term,
                        italic=italic,
                        category=category,
                        note=note,
                        language=language,
                        case_sensitive=case_sensitive,
                        priority=priority,
                        pattern=_build_pattern(term, case_sensitive),
                    )
                )
        # Specificity: term lebih panjang didahulukan.
        entries.sort(key=lambda e: (-len(e.term), -e.priority, e.term.lower()))
        return entries

    def _load_exceptions(self) -> set:
        if not self.exceptions_path or not self.exceptions_path.exists():
            return set()
        out = set()
        with self.exceptions_path.open(
            "r", encoding="utf-8", newline=""
        ) as f:
            reader = csv.DictReader(f)
            for row in reader:
                w = (row.get("word") or "").strip().lower()
                if w:
                    out.add(w)
        return out

    @classmethod
    def from_data(
        cls,
        entries: List[dict],
        exceptions: Optional[set] = None,
    ) -> "GlossaryService":
        """In-memory untuk test."""
        svc = cls(Path("."))
        loaded: List[GlossaryEntry] = []
        for e in entries:
            term = e.get("term", "").strip()
            if not term:
                continue
            cs = bool(e.get("case_sensitive", False))
            loaded.append(
                GlossaryEntry(
                    term=term,
                    italic=bool(e.get("italic", False)),
                    category=e.get("category", ""),
                    note=e.get("note", ""),
                    language=e.get("language", ""),
                    case_sensitive=cs,
                    priority=int(e.get("priority", 0)),
                    pattern=_build_pattern(term, cs),
                )
            )
        loaded.sort(
            key=lambda e: (-len(e.term), -e.priority, e.term.lower())
        )
        svc.entries = loaded
        svc.exceptions = set(w.lower() for w in (exceptions or set()))
        svc.status = GlossaryStatus(
            loaded=True,
            entry_count=len(loaded),
            exception_count=len(svc.exceptions),
        )
        return svc

    def find_matches(self, text: str) -> List[GlossaryMatch]:
        if not text or not self.entries:
            return []
        raw: List[GlossaryMatch] = []
        for entry in self.entries:
            if entry.term.lower() in self.exceptions:
                continue
            for m in entry.pattern.finditer(text):
                raw.append(
                    GlossaryMatch(
                        term=entry.term,
                        matched_text=m.group(0),
                        char_start=m.start(),
                        char_end=m.end(),
                        entry=entry,
                    )
                )
        if not raw:
            return []
        # Preferensi: start ascending, length descending, term ascending.
        raw.sort(
            key=lambda x: (
                x.char_start,
                -(x.char_end - x.char_start),
                x.term.lower(),
            )
        )
        chosen: List[GlossaryMatch] = []
        for m in raw:
            overlap = any(
                m.char_start < c.char_end and c.char_start < m.char_end
                for c in chosen
            )
            if not overlap:
                chosen.append(m)
        chosen.sort(key=lambda x: x.char_start)
        return chosen


__all__ = [
    "GlossaryEntry", "GlossaryMatch", "GlossaryService", "GlossaryStatus",
]