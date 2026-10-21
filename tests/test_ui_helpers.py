"""Test helper murni UI Phase 7.5. Tidak merender Streamlit."""

from types import SimpleNamespace

import pytest

from src.docxlint.models.change_plan import ChangeItem
from src.docxlint.models.document import Location
from src.docxlint.models.finding import Finding
from src.docxlint.services.docx_reader import read_document
from src.docxlint.services.review_state import SelectionState
from src.docxlint.ui import components as c
from src.docxlint.ui.theme import COLORS, TEXT_PAIRS, build_css, contrast_ratio


def _finding(**kw):
    base = dict(
        finding_id="f1", rule_id="LANG_001", category="spelling",
        severity="medium",
        location=Location("s", "document", "body/p[3]", "paragraph",
                          0, 12, 18),
        original_value="kesalhan", suggested_value="kesalahan",
        reason="Tidak ada di kamus", confidence=0.9,
    )
    base.update(kw)
    return Finding(**base)


# --- theme ---------------------------------------------------------------

def test_contrast_ratio_extremes():
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast_ratio("#FFFFFF", "#FFFFFF") == pytest.approx(1.0)


@pytest.mark.parametrize("fg,bg", TEXT_PAIRS)
def test_text_pairs_meet_wcag_aa(fg, bg):
    assert contrast_ratio(COLORS[fg], COLORS[bg]) >= 4.5


def test_base_warning_success_not_used_for_text():
    # Warna dasar gagal AA untuk teks; karena itu ada varian *_text.
    assert contrast_ratio(COLORS["warning"], COLORS["surface"]) < 4.5
    assert contrast_ratio(COLORS["success"], COLORS["surface"]) < 4.5


def test_contrast_rejects_invalid_hex():
    with pytest.raises(ValueError):
        contrast_ratio("#FFF", "#000000")


def test_build_css_contains_tokens():
    css = build_css()
    assert css.startswith("\n<style>")
    assert COLORS["accent"] in css
    assert "st-key-review_filter_bar" in css


# --- label & badge -------------------------------------------------------

@pytest.mark.parametrize("sev,expected", [
    ("high", COLORS["danger_text"]),
    ("medium", COLORS["warning_text"]),
    ("low", COLORS["accent"]),
    ("info", COLORS["muted_text"]),
    ("weird", COLORS["text"]),
])
def test_severity_color(sev, expected):
    assert c.severity_color(sev) == expected


@pytest.mark.parametrize("conf,expected", [
    (0.92, "Yakin · 0,92"),
    (0.85, "Yakin · 0,85"),
    (0.70, "Cukup yakin · 0,70"),
    (0.10, "Ragu · 0,10"),
])
def test_confidence_label(conf, expected):
    assert c.confidence_label(conf) == expected


def test_badge_text_for_state():
    assert c.badge_text_for_state("not_run") == "Belum diperiksa"
    assert c.badge_text_for_state("done") == "Sudah diperiksa"
    assert c.badge_text_for_state("done", 12) == \
        "Sudah diperiksa · 12 temuan"
    assert c.badge_text_for_state("selected", 3) == "3 dipilih"
    assert c.badge_text_for_state("repair_ready") == "Perbaikan siap diunduh"
    with pytest.raises(ValueError):
        c.badge_text_for_state("nope")


def test_format_location_and_size():
    assert c.format_location("body/p[3]", 0, 12, 18) == \
        "body/p[3] run[0] 12–18"
    assert c.format_file_size(500) == "500 B"
    assert c.format_file_size(1536) == "1.5 KB"
    assert c.format_file_size(128 * 1024) == "128 KB"
    assert c.format_file_size(3 * 1024 * 1024) == "3.0 MB"


def test_status_bar_text():
    assert c.status_bar_text("a.docx", 128 * 1024, 42, 3) == \
        "a.docx • 128 KB • 42 paragraf • 3 tabel"


def test_document_stats_counts_tables(docx_with_table_bytes):
    snap = read_document(docx_with_table_bytes)
    stats = c.document_stats(snap.parts)
    # Sama seperti metrik lama: paragraf di dalam sel ikut dihitung.
    assert stats["paragraphs"] == 5
    assert stats["tables"] == 1
    assert stats["cells"] == 4


def test_check_badges_and_repair_state():
    state = {}
    badges = c.check_badges(state)
    assert [b.label for b in badges] == [
        "Bahasa", "Istilah asing", "Format", "Pilihan", "Perbaikan",
    ]
    assert badges[0].text == "Belum diperiksa"
    assert badges[3].text == "Belum ada yang dipilih"
    assert badges[4].text == "Belum ada perbaikan"

    sel = SelectionState(selected_ids={"a", "b"})
    state = {
        "findings": [_finding()], "selection_state": sel,
        "repair_output_bytes": b"x",
        "repair_report": SimpleNamespace(ok=True),
    }
    badges = c.check_badges(state)
    assert badges[0].text == "Sudah diperiksa · 1 temuan"
    assert badges[3].text == "2 dipilih"
    assert badges[4].tone == "success"

    state["repair_critical"] = True
    assert c.repair_state(state) == "repair_blocked"


def test_stage_progress_marks_single_current():
    steps = c.stage_progress({}, file_ready=True)
    statuses = [s for _, s, _ in steps]
    assert statuses == ["done", "current", "todo", "todo", "todo"]
    stale = {"findings": [_finding()], "repair_output_bytes": b"x"}
    steps = c.stage_progress(stale, file_ready=False)
    assert [s for _, s, _ in steps] == \
        ["current", "todo", "todo", "todo", "todo"]


# --- HTML escaping -------------------------------------------------------

def test_finding_header_escapes_document_text():
    f = _finding(original_value="<script>x</script>",
                 suggested_value="<b>y</b>", reason="a & b")
    html = c.finding_header_html(f)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;y&lt;/b&gt;" in html
    assert "a &amp; b" in html
    assert "body/p[3] run[0] 12–18" in html


def test_change_plan_table_escapes_and_labels():
    item = ChangeItem(
        change_id="c", finding_id="f", operation="replace_text",
        part="document", block_path="body/p[0]", run_index=0,
        char_start=0, char_end=3, original_value="<i>",
        replacement="ok", snapshot_hash="h",
    )
    html = c.change_plan_table_html([item])
    assert "&lt;i&gt;" in html
    assert "Valid" in html and "Ganti teks" in html
