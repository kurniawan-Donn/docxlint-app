from src.docxlint.models.document import Block, Run
from src.docxlint.services.italic_inspector import inspect_italic


def _block(runs, style_name=None):
    return Block(
        block_path="body/p[0]",
        block_type="paragraph",
        part="document",
        text="".join(r.text for r in runs),
        runs=runs,
        style_name=style_name,
    )


def _run(text, italic, start, end, complex_=False):
    return Run(
        run_index=0, text=text,
        char_start=start, char_end=end,
        is_complex_run=complex_, italic=italic,
    )


def test_fully_italicized():
    b = _block([_run("streaming", True, 0, 9)])
    assert inspect_italic(b, 0, 9)[0] == "fully_italicized"


def test_not_italicized():
    b = _block([_run("streaming", False, 0, 9)])
    assert inspect_italic(b, 0, 9)[0] == "not_italicized"


def test_partially_italicized_across_runs():
    b = _block([
        _run("stream", True, 0, 6),
        _run("ing", False, 6, 9),
    ])
    assert inspect_italic(b, 0, 9)[0] == "partially_italicized"


def test_unknown_when_italic_none():
    b = _block([_run("streaming", None, 0, 9)])
    state, reason = inspect_italic(b, 0, 9)
    assert state == "unknown"
    assert reason == "style_unresolved"


def test_emphasis_style_resolves():
    b = _block([_run("streaming", None, 0, 9)], style_name="Emphasis")
    assert inspect_italic(b, 0, 9)[0] == "fully_italicized"


def test_complex_run_skipped():
    b = _block([_run("streaming", True, 0, 9, complex_=True)])
    state, reason = inspect_italic(b, 0, 9)
    assert state == "skipped"
    assert reason == "run_complex"


def test_no_overlap():
    b = _block([_run("streaming", True, 0, 9)])
    assert inspect_italic(b, 20, 25)[0] == "unknown"