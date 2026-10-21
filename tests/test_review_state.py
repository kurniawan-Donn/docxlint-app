"""Test Phase 5 review workflow. Pure functions, tanpa Streamlit."""

import pytest

from src.docxlint.models.document import Location
from src.docxlint.models.finding import (
    APPLICATION_NOT_APPLIED,
    APPLICATION_SKIPPED,
    CATEGORY_FOREIGN_TERM,
    CATEGORY_ITALIC_FORMATTING,
    CATEGORY_SPELLING,
    CATEGORY_UNKNOWN_WORD,
    Finding,
    REVIEW_ACCEPTED,
    REVIEW_CONFLICT,
    REVIEW_PENDING,
    make_finding_id,
)
from src.docxlint.services.review_state import (
    ReviewFilters,
    SelectionState,
    confidence_band,
    filter_findings,
    is_selectable,
    summarize,
)


def _loc():
    return Location(
        snapshot_id="s1",
        part="document",
        block_path="body/p[0]",
        block_type="paragraph",
        run_index=0,
        char_start=0,
        char_end=4,
    )


def _finding(
    category=CATEGORY_SPELLING,
    severity="medium",
    confidence=0.90,
    original="salahh",
    suggested="salah",
    reason="mirip kamus",
    rule_id="SPELL_001",
    review_status=REVIEW_PENDING,
    application_status=APPLICATION_NOT_APPLIED,
):
    return Finding(
        finding_id=make_finding_id(),
        rule_id=rule_id,
        category=category,
        severity=severity,
        location=_loc(),
        original_value=original,
        suggested_value=suggested,
        reason=reason,
        confidence=confidence,
        review_status=review_status,
        application_status=application_status,
    )


# --- confidence_band ---

def test_confidence_band_boundaries():
    assert confidence_band(0.85) == "high"
    assert confidence_band(0.99) == "high"
    assert confidence_band(0.84) == "medium"
    assert confidence_band(0.60) == "medium"
    assert confidence_band(0.59) == "low"
    assert confidence_band(0.10) == "low"


# --- filter_findings ---

def test_filter_by_category():
    a = _finding(category=CATEGORY_SPELLING)
    b = _finding(category=CATEGORY_UNKNOWN_WORD)
    got = filter_findings(
        [a, b],
        ReviewFilters(categories={CATEGORY_SPELLING}),
        set(),
    )
    assert got == [a]


def test_filter_by_severity():
    a = _finding(severity="medium")
    b = _finding(severity="low")
    got = filter_findings(
        [a, b], ReviewFilters(severities={"low"}), set(),
    )
    assert got == [b]


def test_filter_by_review_status():
    a = _finding(review_status=REVIEW_PENDING)
    b = _finding(review_status=REVIEW_ACCEPTED)
    got = filter_findings(
        [a, b], ReviewFilters(review_statuses={REVIEW_ACCEPTED}), set(),
    )
    assert got == [b]


def test_filter_by_application_status():
    a = _finding(application_status=APPLICATION_NOT_APPLIED)
    b = _finding(application_status=APPLICATION_SKIPPED)
    got = filter_findings(
        [a, b],
        ReviewFilters(application_statuses={APPLICATION_SKIPPED}),
        set(),
    )
    assert got == [b]


def test_filter_by_confidence_band():
    high = _finding(confidence=0.90)
    med = _finding(confidence=0.70)
    low = _finding(confidence=0.40)
    got = filter_findings(
        [high, med, low],
        ReviewFilters(confidence_bands={"medium"}),
        set(),
    )
    assert got == [med]


def test_filter_selection_state():
    a = _finding()
    b = _finding()
    got_sel = filter_findings(
        [a, b], ReviewFilters(selection="selected"), {a.finding_id},
    )
    assert got_sel == [a]
    got_unsel = filter_findings(
        [a, b], ReviewFilters(selection="unselected"), {a.finding_id},
    )
    assert got_unsel == [b]


def test_filter_search_original():
    a = _finding(original="kucing")
    b = _finding(original="anjing")
    got = filter_findings(
        [a, b], ReviewFilters(search_text="kuc"), set(),
    )
    assert got == [a]


def test_filter_search_suggestion():
    a = _finding(suggested="makan")
    b = _finding(suggested="minum")
    got = filter_findings(
        [a, b], ReviewFilters(search_text="minum"), set(),
    )
    assert got == [b]


def test_filter_search_rule_id():
    a = _finding(rule_id="SPELL_001")
    b = _finding(rule_id="UNKNOWN_001")
    got = filter_findings(
        [a, b], ReviewFilters(search_text="unknown"), set(),
    )
    assert got == [b]


def test_filter_search_reason():
    a = _finding(reason="ejaan umum")
    b = _finding(reason="istilah teknis")
    got = filter_findings(
        [a, b], ReviewFilters(search_text="teknis"), set(),
    )
    assert got == [b]


def test_filter_combined():
    a = _finding(category=CATEGORY_SPELLING, confidence=0.90,
                 original="salahh")
    b = _finding(category=CATEGORY_SPELLING, confidence=0.40,
                 original="salahh")
    c = _finding(category=CATEGORY_UNKNOWN_WORD, confidence=0.90,
                 original="salahh")
    got = filter_findings(
        [a, b, c],
        ReviewFilters(
            categories={CATEGORY_SPELLING},
            confidence_bands={"high"},
            search_text="salahh",
        ),
        set(),
    )
    assert got == [a]


def test_filter_empty_results():
    a = _finding(original="hello")
    got = filter_findings(
        [a], ReviewFilters(search_text="zzz"), set(),
    )
    assert got == []


def test_filter_preserves_other_findings_selection():
    """Filter tidak menghapus selection untuk finding di luar visible set."""
    a = _finding()
    b = _finding()
    state = SelectionState(snapshot_id="s1")
    state.select_many({a.finding_id, b.finding_id})
    visible = filter_findings(
        [a, b], ReviewFilters(selection="unselected"), state.selected_ids,
    )
    assert visible == []
    # Selection tetap utuh
    assert state.selected_ids == {a.finding_id, b.finding_id}


# --- is_selectable ---

def test_is_selectable_conflict():
    f = _finding(review_status=REVIEW_CONFLICT)
    assert is_selectable(f) is False


def test_is_selectable_skipped():
    f = _finding(application_status=APPLICATION_SKIPPED)
    assert is_selectable(f) is False


def test_is_selectable_normal():
    assert is_selectable(_finding()) is True


# --- SelectionState ---

def test_selection_toggle():
    s = SelectionState(snapshot_id="s1")
    s.toggle("a")
    assert "a" in s.selected_ids
    s.toggle("a")
    assert "a" not in s.selected_ids


def test_selection_select_many():
    s = SelectionState(snapshot_id="s1")
    s.select_many(["a", "b", "c"])
    assert s.selected_ids == {"a", "b", "c"}


def test_selection_deselect_many():
    s = SelectionState(snapshot_id="s1")
    s.select_many(["a", "b", "c"])
    s.deselect_many(["b"])
    assert s.selected_ids == {"a", "c"}


def test_selection_clear():
    s = SelectionState(snapshot_id="s1")
    s.select_many(["a", "b"])
    s.clear_selection()
    assert s.selected_ids == set()


def test_selection_snapshot_change_resets():
    s = SelectionState()
    assert s.ensure_snapshot("snap-1") is True
    s.select_many(["a", "b"])
    assert s.ensure_snapshot("snap-1") is False
    assert s.selected_ids == {"a", "b"}
    assert s.ensure_snapshot("snap-2") is True
    assert s.selected_ids == set()


def test_selection_same_snapshot_preserves():
    s = SelectionState(snapshot_id="snap-1")
    s.select_many(["a"])
    assert s.ensure_snapshot("snap-1") is False
    assert s.selected_ids == {"a"}


def test_selection_does_not_modify_finding():
    f = _finding()
    s = SelectionState(snapshot_id="s1")
    s.toggle(f.finding_id)
    # Finding tidak disentuh oleh selection.
    assert f.review_status == REVIEW_PENDING
    assert f.application_status == APPLICATION_NOT_APPLIED


def test_review_status_independent_of_selection():
    f = _finding()
    s = SelectionState(snapshot_id="s1")
    f.review_status = REVIEW_ACCEPTED
    assert f.finding_id not in s.selected_ids
    s.toggle(f.finding_id)
    assert f.review_status == REVIEW_ACCEPTED  # tidak berubah


# --- summarize ---

def test_summarize_total_unique():
    a = _finding()
    b = _finding()
    s = summarize([a, b, a], set())
    assert s["total"] == 2


def test_summarize_categories():
    a = _finding(category=CATEGORY_SPELLING)
    b = _finding(category=CATEGORY_UNKNOWN_WORD)
    c = _finding(category=CATEGORY_FOREIGN_TERM)
    d = _finding(category=CATEGORY_ITALIC_FORMATTING)
    s = summarize([a, b, c, d], set())
    assert s["spelling"] == 1
    assert s["unknown_word"] == 1
    assert s["foreign_term"] == 1
    assert s["italic_formatting"] == 1


def test_summarize_selected():
    a = _finding()
    b = _finding()
    s = summarize([a, b], {a.finding_id})
    assert s["selected"] == 1


def test_summarize_uncertain():
    a = _finding(confidence=0.90)
    b = _finding(confidence=0.40)
    s = summarize([a, b], set())
    assert s["uncertain"] == 1


def test_summarize_duplicate_ids():
    f = _finding()
    s = summarize([f, f, f], set())
    assert s["total"] == 1


def test_finding_default_status_pending():
    f = _finding()
    assert f.review_status == REVIEW_PENDING
    assert f.application_status == APPLICATION_NOT_APPLIED