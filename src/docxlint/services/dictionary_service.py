"""Layanan kamus lokal.

DECISION-018: wordlist kurasi manual + adapter untuk penggantian.
DECISION-025: protected terms di-suppress total sebelum Rule A/B.
Tidak ada network call. Tidak ada redistribusi KBBI.

Format file mengikuti docs/config_schema.md:
- dictionary_id.txt: satu kata per baris
- whitelist.txt: satu kata per baris
- exceptions.csv: kolom word, reason
- terminology.csv: kolom term, italic, category, note
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from ..config import (
    DEFAULT_PROTECTED_TERMS,
    DICTIONARY_FILE,
    EXCEPTIONS_FILE,
    TERMINOLOGY_FILE,
    WHITELIST_FILE,
)


@dataclass
class DictionaryStatus:
    loaded: bool
    source_path: Optional[str]
    word_count: int
    whitelist_count: int
    exception_count: int
    terminology_count: int
    error: Optional[str] = None


# Afiks bahasa Indonesia (heuristik konservatif).
_INDONESIAN_PREFIXES = (
    "menge", "meng", "meny", "men", "mem", "me",
    "peng", "peny", "pen", "pem", "pe", "per",
    "ber", "be", "ter", "te",
    "di", "ke", "se",
)

_INDONESIAN_SUFFIXES = (
    "kannya", "nya", "lah", "kah", "pun",
    "kan", "an", "i",
)


class DictionaryService:
    """Kamus lokal + whitelist + exceptions + terminology."""

    def __init__(self, config_dir: Path) -> None:
        self.config_dir = Path(config_dir)
        self.words: FrozenSet[str] = frozenset()
        self.whitelist: FrozenSet[str] = frozenset()
        self.exceptions: Dict[str, str] = {}
        self.terminology: Dict[str, dict] = {}
        self.status = DictionaryStatus(
            loaded=False,
            source_path=None,
            word_count=0,
            whitelist_count=0,
            exception_count=0,
            terminology_count=0,
        )

    # --- loading -------------------------------------------------------

    def load(self) -> DictionaryStatus:
        try:
            self.words = self._load_wordlist(
                self.config_dir / DICTIONARY_FILE
            )
            self.whitelist = self._load_wordlist(
                self.config_dir / WHITELIST_FILE
            )
            self.exceptions = self._load_exceptions(
                self.config_dir / EXCEPTIONS_FILE
            )
            self.terminology = self._load_terminology(
                self.config_dir / TERMINOLOGY_FILE
            )
            self.status = DictionaryStatus(
                loaded=bool(self.words),
                source_path=str(self.config_dir / DICTIONARY_FILE),
                word_count=len(self.words),
                whitelist_count=len(self.whitelist),
                exception_count=len(self.exceptions),
                terminology_count=len(self.terminology),
                error=None if self.words else "Wordlist kosong atau hilang.",
            )
        except FileNotFoundError as exc:
            self.status = DictionaryStatus(
                loaded=False,
                source_path=None,
                word_count=0,
                whitelist_count=0,
                exception_count=0,
                terminology_count=0,
                error=f"File tidak ditemukan: {exc.filename}",
            )
        except Exception as exc:  # defensive, tanpa isi dokumen
            self.status = DictionaryStatus(
                loaded=False,
                source_path=None,
                word_count=0,
                whitelist_count=0,
                exception_count=0,
                terminology_count=0,
                error=f"Gagal memuat kamus: {type(exc).__name__}",
            )
        return self.status

    def _load_wordlist(self, path: Path) -> FrozenSet[str]:
        if not path.exists():
            return frozenset()
        words = set()
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                words.add(line.lower())
        return frozenset(words)

    def _load_exceptions(self, path: Path) -> Dict[str, str]:
        if not path.exists():
            return {}
        result: Dict[str, str] = {}
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = (row.get("word") or "").strip().lower()
                if not word:
                    continue
                result[word] = (row.get("reason") or "").strip()
        return result

    def _load_terminology(self, path: Path) -> Dict[str, dict]:
        if not path.exists():
            return {}
        result: Dict[str, dict] = {}
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                term = (row.get("term") or "").strip().lower()
                if not term:
                    continue
                italic = (row.get("italic") or "").strip().lower() in (
                    "true", "1", "yes", "y",
                )
                result[term] = {
                    "italic": italic,
                    "category": (row.get("category") or "").strip(),
                    "note": (row.get("note") or "").strip(),
                }
        return result

    @classmethod
    def from_data(
        cls,
        words: Iterable[str],
        whitelist: Iterable[str] = (),
        exceptions: Optional[Dict[str, str]] = None,
        terminology: Optional[Dict[str, dict]] = None,
    ) -> "DictionaryService":
        """Konstruktor in-memory untuk test, tanpa file."""
        svc = cls(Path("."))
        svc.words = frozenset(w.lower() for w in words)
        svc.whitelist = frozenset(w.lower() for w in whitelist)
        svc.exceptions = {
            k.lower(): v for k, v in (exceptions or {}).items()
        }
        svc.terminology = {
            k.lower(): v for k, v in (terminology or {}).items()
        }
        svc.status = DictionaryStatus(
            loaded=True,
            source_path="<in-memory>",
            word_count=len(svc.words),
            whitelist_count=len(svc.whitelist),
            exception_count=len(svc.exceptions),
            terminology_count=len(svc.terminology),
        )
        return svc

    # --- lookup --------------------------------------------------------

    @staticmethod
    def _normalize(word: str) -> str:
        """Normalisasi case-insensitive untuk lookup.

        Tidak mengubah teks dokumen; hanya untuk pencocokan internal.
        """
        return word.strip().lower()

    def is_known(self, word: str) -> bool:
        w = self._normalize(word)
        return (
            w in DEFAULT_PROTECTED_TERMS
            or w in self.words
            or w in self.whitelist
            or w in self.exceptions
            or w in self.terminology
        )

    def is_protected(self, word: str) -> bool:
        w = self._normalize(word)
        return (
            w in DEFAULT_PROTECTED_TERMS
            or w in self.whitelist
            or w in self.exceptions
            or w in self.terminology
        )

    def lookup_root(self, word: str) -> Optional[str]:
        """Kembalikan root jika word adalah derivasi morfologis kata dasar."""
        w = self._normalize(word)
        if w in self.words:
            return w

        for prefix in _INDONESIAN_PREFIXES:
            if not w.startswith(prefix):
                continue
            rest = w[len(prefix):]
            if len(rest) < 3:
                continue
            if rest in self.words:
                return rest
            for suffix in _INDONESIAN_SUFFIXES:
                if not rest.endswith(suffix):
                    continue
                base = rest[: -len(suffix)]
                if len(base) >= 3 and base in self.words:
                    return base

        for suffix in _INDONESIAN_SUFFIXES:
            if not w.endswith(suffix):
                continue
            base = w[: -len(suffix)]
            if len(base) >= 3 and base in self.words:
                return base

        return None

    # --- saran ---------------------------------------------------------

    def suggest(
        self,
        word: str,
        max_n: int = 3,
        max_distance: int = 2,
    ) -> List[Tuple[str, int]]:
        """Saran deterministik dari kamus. Urut (distance, alfabetis)."""
        w = self._normalize(word)
        candidates: List[Tuple[str, int]] = []
        for dict_word in self.words:
            if abs(len(dict_word) - len(w)) > max_distance:
                continue
            d = _levenshtein(w, dict_word, max_distance)
            if d <= max_distance:
                candidates.append((dict_word, d))
        candidates.sort(key=lambda x: (x[1], x[0]))
        return candidates[:max_n]


def _levenshtein(a: str, b: str, max_distance: int = 99) -> int:
    """Levenshtein dengan batas atas; > max_distance bila lewat."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if abs(len(a) - len(b)) > max_distance:
        return max_distance + 1

    m, n = len(a), len(b)
    if m < n:
        a, b = b, a
        m, n = n, m

    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        row_min = cur[0]
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if cur[j] < row_min:
                row_min = cur[j]
        if row_min > max_distance:
            return max_distance + 1
        prev = cur
    return prev[n]


__all__ = ["DictionaryService", "DictionaryStatus"]