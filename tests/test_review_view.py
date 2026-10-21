"""Test helper murni tampilan Tinjauan (Phase 7.5)."""

from src.docxlint.models.document import Location
from src.docxlint.models.finding import Finding
from src.docxlint.ui.components import finding_header_html
from src.docxlint.ui.review_view import (
    SCOPE_ACTIONABLE,
    SCOPE_ALL,
    SCOPE_INFO,
    filter_scope,
    group_findings,
    is_actionable,
    page_range_text,
    paginate,
    sort_by_priority,
)


def _f(fid, category="spelling", original="kata", suggested=None,
       severity="medium", confidence=0.9, path="body/p[0]", start=0,
       metadata=None):
    return Finding(
        finding_id=fid, rule_id="R", category=category, severity=severity,
        location=Location("s", "document", path, "paragraph", 0,
                          start, start + len(original)),
        original_value=original, suggested_value=suggested,
        reason="alasan", confidence=confidence,
        metadata=metadata or {},
    )


def test_is_actionable_matches_repair_rules():
    assert is_actionable(_f("a", suggested="kata"))
    assert not is_actionable(_f("b", suggested=None))
    assert not is_actionable(_f("c", category="unknown_word",
                                suggested="x"))
    assert is_actionable(_f("d", category="italic_formatting",
                            metadata={"expected_italic": True}))
    assert not is_actionable(_f("e", category="italic_formatting",
                                metadata={"expected_italic": False}))
    assert not is_actionable(_f("f", category="foreign_term"))


def test_filter_scope_partitions():
    items = [_f("a", suggested="x"), _f("b", category="unknown_word")]
    assert [f.finding_id for f in filter_scope(items, SCOPE_ACTIONABLE)] \
        == ["a"]
    assert [f.finding_id for f in filter_scope(items, SCOPE_INFO)] == ["b"]
    assert len(filter_scope(items, SCOPE_ALL)) == 2


def test_sort_by_priority():
    items = [
        _f("info", category="unknown_word", severity="high"),
        _f("low", suggested="x", severity="low"),
        _f("high_weak", suggested="x", severity="high", confidence=0.6),
        _f("high_strong", suggested="x", severity="high", confidence=0.95),
    ]
    order = [f.finding_id for f in sort_by_priority(items)]
    assert order == ["high_strong", "high_weak", "low", "info"]


def test_group_findings_merges_same_word_case_insensitive():
    items = [
        _f("a", category="unknown_word", original="lanjut", path="body/p[1]"),
        _f("b", category="unknown_word", original="Lanjut", path="body/p[4]"),
        _f("c", category="unknown_word", original="tindak"),
        # Kata sama, kategori beda -> kelompok terpisah.
        _f("d", category="spelling", original="lanjut", suggested="lanjur"),
    ]
    groups = group_findings(items)
    by_ids = sorted(sorted(g.finding_ids) for g in groups)
    assert by_ids == [["a", "b"], ["c"], ["d"]]
    # Actionable (spelling dengan saran) di urutan pertama.
    assert groups[0].finding_ids == ["d"]
    # Di antara informasi, kelompok besar lebih dulu.
    assert groups[1].count == 2


def test_group_ids_stable_and_distinct():
    a = group_findings([_f("a", original="x")])[0].group_id
    b = group_findings([_f("b", original="x")])[0].group_id
    c = group_findings([_f("c", original="y")])[0].group_id
    assert a == b
    assert a != c


def test_paginate_clamps():
    items = list(range(45))
    page_items, page, total = paginate(items, 1, 20)
    assert page_items == list(range(20)) and total == 3
    page_items, page, _ = paginate(items, 99, 20)
    assert page == 3 and page_items == list(range(40, 45))
    _, page, total = paginate([], 5, 20)
    assert page == 1 and total == 1
    _, page, _ = paginate(items, 0, 20)
    assert page == 1


def test_page_range_text():
    assert page_range_text(1, 20, 45) == "1–20 dari 45"
    assert page_range_text(3, 20, 45) == "41–45 dari 45"
    assert page_range_text(1, 20, 0) == "0 dari 0"


def test_group_header_shows_occurrences():
    html = finding_header_html(_f("a", original="lanjut"), occurrences=3)
    assert "3 lokasi" in html
    assert "Lokasi pertama dari 3" in html
    single = finding_header_html(_f("a", original="lanjut"))
    assert "lokasi" not in single.split("Lokasi:")[0]
