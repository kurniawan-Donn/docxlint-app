"""Tokenizer untuk teks Indonesia + Inggris campuran.

- Mempertahankan ejaan & kapitalisasi asli.
- Menjaga offset karakter (char_start/char_end).
- Melewati URL, email, path, tanggal, angka.
- Tidak mengubah teks dokumen.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple

_URL_PATTERN = re.compile(r"(?:https?|ftp)://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PATH_PATTERN = re.compile(
    r"[A-Za-z]:\\[^\s]+|(?:\.{0,2}/)+(?:[\w.-]+/)*[\w.-]+"
)
_DATE_PATTERN = re.compile(r"\b\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b")
_NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")

# Kata: huruf Unicode, opsional dengan apostrof/hyphen internal.
_WORD_PATTERN = re.compile(
    r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE
)


@dataclass(frozen=True)
class Token:
    text: str
    char_start: int
    char_end: int
    normalized: str


def _overlaps(start: int, end: int, spans: List[Tuple[int, int]]) -> bool:
    for s, e in spans:
        if start < e and s < end:
            return True
    return False


def tokenize(text: str) -> List[Token]:
    if not text:
        return []

    skip_spans: List[Tuple[int, int]] = []
    for pattern in (
        _URL_PATTERN, _EMAIL_PATTERN, _PATH_PATTERN,
        _DATE_PATTERN, _NUMBER_PATTERN,
    ):
        for m in pattern.finditer(text):
            skip_spans.append((m.start(), m.end()))

    tokens: List[Token] = []
    for m in _WORD_PATTERN.finditer(text):
        start, end = m.start(), m.end()
        if _overlaps(start, end, skip_spans):
            continue
        original = m.group(0)
        tokens.append(
            Token(
                text=original,
                char_start=start,
                char_end=end,
                normalized=original.lower(),
            )
        )
    return tokens


__all__ = ["Token", "tokenize"]