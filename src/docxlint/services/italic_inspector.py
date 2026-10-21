"""Inspeksi status italic untuk rentang karakter dalam satu Block.

Menggunakan Run.italic dari reader Phase 2. Jika None (inherited),
coba heuristik style nama; jika gagal -> unknown.

Run kompleks (DECISION-021) -> skipped.
"""

from typing import Tuple

from ..models.document import Block
from ..models.finding import (
    ITALIC_FULLY,
    ITALIC_NOT,
    ITALIC_PARTIALLY,
    ITALIC_SKIPPED,
    ITALIC_UNKNOWN,
)

_ITALIC_STYLE_HINTS = ("emphasis", "italic", "emphasisstrong")


def inspect_italic(
    block: Block, char_start: int, char_end: int
) -> Tuple[str, str]:
    """Kembalikan (state, reason)."""
    if char_start >= char_end:
        return ITALIC_UNKNOWN, "empty_range"

    overlapping = []
    for r in block.runs:
        if r.char_end <= char_start or r.char_start >= char_end:
            continue
        if r.is_complex_run:
            return ITALIC_SKIPPED, "run_complex"
        overlapping.append(r)

    if not overlapping:
        return ITALIC_UNKNOWN, "no_overlap"

    raw_states = [r.italic for r in overlapping]
    if any(s is None for s in raw_states):
        style_name = (block.style_name or "").lower()
        if any(h in style_name for h in _ITALIC_STYLE_HINTS):
            raw_states = [True if s is None else s for s in raw_states]
        else:
            return ITALIC_UNKNOWN, "style_unresolved"

    if all(s is True for s in raw_states):
        return ITALIC_FULLY, ""
    if all(s is False for s in raw_states):
        return ITALIC_NOT, ""
    return ITALIC_PARTIALLY, ""


__all__ = ["inspect_italic"]