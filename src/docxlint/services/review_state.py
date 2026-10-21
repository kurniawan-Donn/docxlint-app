"""Pure helpers untuk review workflow Phase 5.

Tidak bergantung Streamlit. Dapat ditest standalone.
Tidak mengubah dokumen. Tidak menulis ke disk.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set

from ..models.finding import (
    REVIEW_CONFLICT,
    REVIEW_PENDING,
    Finding,
)

CONF_HIGH_MIN = 0.85
CONF_MEDIUM_MIN = 0.60


def confidence_band(confidence: float) -> str:
    """Klasifikasi sesuai DECISION-008."""
    if confidence >= CONF_HIGH_MIN:
        return "high"
    if confidence >= CONF_MEDIUM_MIN:
        return "medium"
    return "low"


@dataclass
class ReviewFilters:
    categories: Set[str] = field(default_factory=set)
    severities: Set[str] = field(default_factory=set)
    review_statuses: Set[str] = field(default_factory=set)
    application_statuses: Set[str] = field(default_factory=set)
    confidence_bands: Set[str] = field(default_factory=set)
    selection: str = "all"  # "all" | "selected" | "unselected"
    search_text: str = ""


def _matches_search(f: Finding, needle: str) -> bool:
    if not needle:
        return True
    n = needle.lower()
    haystack = " ".join(
        [
            f.original_value or "",
            f.suggested_value or "",
            f.rule_id or "",
            f.reason or "",
        ]
    ).lower()
    return n in haystack


def is_selectable(f: Finding) -> bool:
    """Finding yang tidak dapat dipilih untuk aksi lanjutan.

    - review_status == 'conflict' -> tidak dapat dipilih.
    - application_status == 'skipped' / 'conflict' -> tidak dapat dipilih.
    """
    if f.review_status == REVIEW_CONFLICT:
        return False
    if f.application_status in ("skipped", "conflict"):
        return False
    return True


def filter_findings(
    findings: Iterable[Finding],
    filters: ReviewFilters,
    selected_ids: Set[str],
) -> List[Finding]:
    out: List[Finding] = []
    needle = (filters.search_text or "").strip().lower()
    for f in findings:
        if filters.categories and f.category not in filters.categories:
            continue
        if filters.severities and f.severity not in filters.severities:
            continue
        if filters.review_statuses and \
                f.review_status not in filters.review_statuses:
            continue
        if filters.application_statuses and \
                f.application_status not in filters.application_statuses:
            continue
        if filters.confidence_bands and \
                confidence_band(f.confidence) not in filters.confidence_bands:
            continue
        if needle and not _matches_search(f, needle):
            continue
        is_sel = f.finding_id in selected_ids
        if filters.selection == "selected" and not is_sel:
            continue
        if filters.selection == "unselected" and is_sel:
            continue
        out.append(f)
    return out


@dataclass
class SelectionState:
    """State seleksi per snapshot.

    - Key selection: finding_id (bukan posisi list).
    - Reset otomatis bila snapshot_id berubah.
    """

    snapshot_id: str = ""
    selected_ids: Set[str] = field(default_factory=set)

    def ensure_snapshot(self, snapshot_id: str) -> bool:
        """Return True jika snapshot berubah dan state di-reset."""
        if self.snapshot_id != snapshot_id:
            self.snapshot_id = snapshot_id
            self.selected_ids.clear()
            return True
        return False

    def toggle(self, finding_id: str) -> None:
        if finding_id in self.selected_ids:
            self.selected_ids.discard(finding_id)
        else:
            self.selected_ids.add(finding_id)

    def select_many(self, finding_ids: Iterable[str]) -> None:
        self.selected_ids.update(finding_ids)

    def deselect_many(self, finding_ids: Iterable[str]) -> None:
        for fid in finding_ids:
            self.selected_ids.discard(fid)

    def clear_selection(self) -> None:
        self.selected_ids.clear()


def summarize(
    findings: Iterable[Finding],
    selected_ids: Set[str],
) -> Dict[str, int]:
    """Hitung metrik dashboard.

    Total = jumlah unik finding_id (anti double-counting).
    """
    seen: Set[str] = set()
    total = 0
    by_cat: Dict[str, int] = {}
    uncertain = 0
    skipped = 0
    conflicts = 0
    selected = 0
    for f in findings:
        if f.finding_id in seen:
            continue
        seen.add(f.finding_id)
        total += 1
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
        if f.confidence < CONF_HIGH_MIN:
            uncertain += 1
        if f.application_status == "skipped":
            skipped += 1
        if f.review_status == REVIEW_CONFLICT:
            conflicts += 1
        if f.finding_id in selected_ids:
            selected += 1
    return {
        "total": total,
        "spelling": by_cat.get("spelling", 0),
        "unknown_word": by_cat.get("unknown_word", 0),
        "foreign_term": by_cat.get("foreign_term", 0),
        "italic_formatting": by_cat.get("italic_formatting", 0),
        "uncertain": uncertain,
        "skipped": skipped,
        "conflicts": conflicts,
        "selected": selected,
    }


__all__ = [
    "ReviewFilters",
    "SelectionState",
    "confidence_band",
    "filter_findings",
    "is_selectable",
    "summarize",
]