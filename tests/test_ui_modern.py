"""Test helper murni tampilan modern Phase 7.5 (tema, stepper, hero)."""

from types import SimpleNamespace

import pytest

from src.docxlint.services.review_state import SelectionState
from src.docxlint.ui import components as c
from src.docxlint.ui.runtime import PUBLIC_DEMO_ENV, is_public_demo
from src.docxlint.ui.theme import (
    DARK,
    LIGHT,
    TEXT_PAIRS,
    build_css,
    contrast_ratio,
    css_variables,
    css_variables_auto,
    normalize_mode,
)


@pytest.mark.parametrize("fg,bg", TEXT_PAIRS)
def test_dark_text_pairs_meet_wcag_aa(fg, bg):
    assert contrast_ratio(DARK[fg], DARK[bg]) >= 4.5


def test_palettes_have_same_tokens():
    assert set(LIGHT) == set(DARK)


def test_css_variables_block():
    block = css_variables({"accent_soft": "#000000"})
    assert block == "  --dl-accent-soft: #000000;\n"


def test_build_css_modes():
    light = build_css("light")
    dark = build_css("dark")
    auto = build_css(None)
    assert LIGHT["bg"] in light and DARK["bg"] not in light
    assert DARK["bg"] in dark and LIGHT["bg"] not in dark
    assert f"light-dark({LIGHT['bg']}, {DARK['bg']})" in auto
    assert "@supports (color: light-dark(#000, #fff))" in auto


def test_css_variables_auto_pairs_every_token():
    block = css_variables_auto(LIGHT, DARK)
    assert block.count("light-dark(") == len(LIGHT)


def test_normalize_mode():
    assert normalize_mode("dark") == "dark"
    assert normalize_mode("light") == "light"
    assert normalize_mode(None) is None
    assert normalize_mode("sepia") is None


@pytest.mark.parametrize("value,expected", [
    ("1", True), ("true", True), ("Ya", True), (" on ", True),
    ("0", False), ("", False), ("no", False),
])
def test_is_public_demo(value, expected):
    assert is_public_demo({PUBLIC_DEMO_ENV: value}) is expected


def test_is_public_demo_missing():
    assert is_public_demo({}) is False


def test_stepper_steps_initial_and_progress():
    steps = c.stepper_steps({}, file_ready=True)
    assert [s["name"] for s in steps] == [
        "Ringkasan", "Pemeriksaan", "Tinjauan", "Perbaikan", "Ekspor",
    ]
    assert [s["status"] for s in steps] == \
        ["done", "current", "todo", "todo", "todo"]

    state = {
        "findings": [object()] * 3,
        "foreign_findings": [object()] * 2,
        "selection_state": SelectionState(selected_ids={"a"}),
        "repair_output_bytes": b"x",
        "repair_report": SimpleNamespace(ok=True),
    }
    steps = c.stepper_steps(state, file_ready=True)
    assert steps[1]["sub"] == "2/3 cek · 5 temuan"
    assert steps[2]["sub"] == "1 dipilih"
    assert steps[4]["sub"] == "Siap diunduh"
    assert all(s["status"] == "done" for s in steps)


def test_stepper_steps_blocked_repair():
    state = {
        "findings": [], "selection_state": SelectionState(selected_ids={"a"}),
        "repair_output_bytes": b"x",
        "repair_report": SimpleNamespace(ok=False),
    }
    steps = c.stepper_steps(state, file_ready=True)
    assert steps[3]["sub"] == "Ada kegagalan"
    assert steps[4]["sub"] == "Diblokir"


def test_stepper_html_marks_current_step():
    html = c.stepper_html(c.stepper_steps({}, file_ready=True))
    assert html.count("<li") == 5
    assert html.count('aria-current="step"') == 1
    assert "(tahap berikutnya)" in html


def test_hero_html_modes():
    local = c.hero_html(public_demo=False)
    demo = c.hero_html(public_demo=True)
    assert "Diproses lokal" in local and "Demo publik" not in local
    assert "Demo publik" in demo and "Diproses lokal" not in demo


def test_landing_and_footer():
    html = c.landing_html()
    assert html.count('class="dl-feature"') == len(c.LANDING_FEATURES)
    assert "Ekspor" in html
    assert "v1.2.3" in c.footer_html("1.2.3")
    assert "&lt;" in c.footer_html("<x>")
