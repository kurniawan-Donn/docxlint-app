"""Helper murni untuk tampilan Tinjauan (Phase 7.5).

Mengurangi kebisingan daftar temuan tanpa mengubah backend:
- pisah "Perlu tindakan" (bisa diperbaiki otomatis) vs "Informasi",
- kelompokkan temuan dengan kata yang sama,
- urutkan berdasarkan prioritas,
- paginasi.

Tidak bergantung Streamlit.
"""

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple, TypeVar

from ..models.finding import CATEGORY_ITALIC_FORMATTING, CATEGORY_SPELLING

SCOPE_ACTIONABLE = "actionable"
SCOPE_INFO = "info"
SCOPE_ALL = "all"

VIEW_GROUPED = "grouped"
VIEW_FLAT = "flat"

PER_PAGE = 20

_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2, "info": 3}

T = TypeVar("T")


def is_actionable(f) -> bool:
    """Temuan yang didukung perbaikan otomatis di tab Perbaikan.

    Sama dengan aturan `render_repair_section`: ejaan dengan saran, atau
    isu italic dengan ekspektasi italic=true.
    """
    if f.category == CATEGORY_SPELLING:
        return bool(f.suggested_value)
    if f.category == CATEGORY_ITALIC_FORMATTING:
        return f.metadata.get("expected_italic") is True
    return False


def filter_scope(findings: Iterable, scope: str) -> List:
    if scope == SCOPE_ACTIONABLE:
        return [f for f in findings if is_actionable(f)]
    if scope == SCOPE_INFO:
        return [f for f in findings if not is_actionable(f)]
    return list(findings)


def priority_key(f) -> Tuple:
    loc = f.location
    return (
        0 if is_actionable(f) else 1,
        _SEVERITY_RANK.get(f.severity, 9),
        -f.confidence,
        loc.part, loc.block_path, loc.run_index, loc.char_start,
    )


def sort_by_priority(findings: Iterable) -> List:
    return sorted(findings, key=priority_key)


@dataclass
class FindingGroup:
    group_id: str
    items: List

    @property
    def lead(self):
        return self.items[0]

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def finding_ids(self) -> List[str]:
        return [f.finding_id for f in self.items]


def group_key(f) -> Tuple[str, str, str]:
    return (
        f.category,
        (f.original_value or "").casefold(),
        (f.suggested_value or "").casefold(),
    )


def _group_id(key: Tuple[str, str, str]) -> str:
    return hashlib.sha1("\x1f".join(key).encode("utf-8")).hexdigest()[:12]


def group_findings(findings: Iterable) -> List[FindingGroup]:
    """Kelompokkan per (kategori, kata, saran); urut prioritas.

    Anggota tiap grup diurutkan prioritas; grup diurutkan berdasarkan
    anggota teratas lalu jumlah anggota (terbanyak dulu).
    """
    buckets: dict = {}
    for f in sort_by_priority(findings):
        buckets.setdefault(group_key(f), []).append(f)
    groups = [FindingGroup(_group_id(k), items) for k, items in buckets.items()]
    groups.sort(key=lambda g: (priority_key(g.lead)[:3], -g.count))
    return groups


def paginate(items: Sequence[T], page: int,
             per_page: int = PER_PAGE) -> Tuple[List[T], int, int]:
    """Return (isi_halaman, halaman_terkoreksi, total_halaman).

    Halaman di-clamp ke rentang valid; minimal 1 halaman.
    """
    total_pages = max(1, -(-len(items) // per_page))
    page = min(max(1, int(page or 1)), total_pages)
    start = (page - 1) * per_page
    return list(items[start:start + per_page]), page, total_pages


def page_range_text(page: int, per_page: int, total: int) -> str:
    """Contoh: '1–20 dari 45'."""
    if total == 0:
        return "0 dari 0"
    start = (page - 1) * per_page + 1
    end = min(page * per_page, total)
    return f"{start}–{end} dari {total}"


__all__ = [
    "SCOPE_ACTIONABLE", "SCOPE_INFO", "SCOPE_ALL",
    "VIEW_GROUPED", "VIEW_FLAT", "PER_PAGE",
    "FindingGroup", "is_actionable", "filter_scope", "priority_key",
    "sort_by_priority", "group_key", "group_findings", "paginate",
    "page_range_text",
]
