import io

import pytest
from docx import Document

from src.docxlint.models.change_plan import (
    APPLIED,
    CONFLICT,
    FAILED,
    NOT_APPLIED,
    OPERATION_APPLY_ITALIC,
    OPERATION_REPLACE_TEXT,
    SKIPPED,
    STALE,
    UNSUPPORTED,
    VALID,
)
from src.docxlint.models.document import Location
from src.docxlint.models.finding import (
    CATEGORY_ITALIC_FORMATTING,
    CATEGORY_SPELLING,
    Finding,
    make_finding_id,
)
from src.docxlint.services.docx_reader import read_document
from src.docxlint.services.docx_repair import (
    RepairEngine,
    _apply_italic_in_run,
    _replace_in_run,
    _resolve_block,
    compute_snapshot_hash,
)


def _make_doc(text="Halo dunia"):
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _finding(location, original, replacement=None,
             category=CATEGORY_SPELLING):
    return Finding(
        finding_id=make_finding_id(),
        rule_id="SPELL_001",
        category=category,
        severity="medium",
        location=location,
        original_value=original,
        suggested_value=replacement,
        reason="test",
        confidence=0.90,
    )


def _loc(snapshot, part="document", block_path="body/p[0]",
         run_index=0, cs=0, ce=5):
    return Location(
        snapshot_id=snapshot.snapshot_id,
        part=part,
        block_path=block_path,
        block_type="paragraph",
        run_index=run_index,
        char_start=cs,
        char_end=ce,
    )


def test_replace_word_in_one_run():
    data = _make_doc("Halo dunia")
    snapshot = read_document(data)
    f = _finding(_loc(snapshot, cs=0, ce=4), "Halo", "Hai")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                              "replacement": "Hai"}}
    )
    engine.validate_plan(plan)
    assert plan.items[0].validation == VALID
    out, plan = engine.apply_plan(plan)
    assert plan.items[0].execution == APPLIED
    doc2 = Document(io.BytesIO(out))
    assert "Hai dunia" in [p.text for p in doc2.paragraphs]


def test_replace_one_occurrence_when_word_appears_twice():
    data = _make_doc("dunia dunia")
    snapshot = read_document(data)
    # Replace the first "dunia" (0..5).
    f = _finding(_loc(snapshot, cs=0, ce=5), "dunia", "bumi")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                              "replacement": "bumi"}}
    )
    engine.validate_plan(plan)
    out, _ = engine.apply_plan(plan)
    doc2 = Document(io.BytesIO(out))
    assert doc2.paragraphs[0].text == "bumi dunia"


def test_original_bytes_unchanged():
    data = _make_doc("Halo dunia")
    snapshot = read_document(data)
    f = _finding(_loc(snapshot, cs=0, ce=4), "Halo", "Hai")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                              "replacement": "Hai"}}
    )
    engine.validate_plan(plan)
    engine.apply_plan(plan)
    # Engine tidak menyentuh byte asli.
    assert engine.original_bytes == data


def test_stale_when_original_text_mismatch():
    data = _make_doc("Halo dunia")
    snapshot = read_document(data)
    f = _finding(_loc(snapshot, cs=0, ce=4), "SALAH", "Hai")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                              "replacement": "Hai"}}
    )
    engine.validate_plan(plan)
    out, plan = engine.apply_plan(plan)
    assert plan.items[0].execution == STALE
    # output kembali ke byte asli
    assert out == data


def test_run_index_out_of_range():
    data = _make_doc("Halo dunia")
    snapshot = read_document(data)
    f = _finding(_loc(snapshot, run_index=99, cs=0, ce=4), "Halo", "Hai")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                              "replacement": "Hai"}}
    )
    engine.validate_plan(plan)
    engine.apply_plan(plan)
    assert plan.items[0].execution == FAILED


def test_overlap_detected():
    data = _make_doc("Halo dunia")
    snapshot = read_document(data)
    f1 = _finding(_loc(snapshot, cs=0, ce=4), "Halo", "Hai")
    f2 = _finding(_loc(snapshot, cs=2, ce=5), "lo d", "xy")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f1, f2],
        {
            f1.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                             "replacement": "Hai"},
            f2.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                             "replacement": "xy"},
        },
    )
    engine.validate_plan(plan)
    validations = {i.validation for i in plan.items}
    assert CONFLICT in validations
    out, plan = engine.apply_plan(plan)
    # Tidak ada yang diterapkan
    for item in plan.items:
        assert item.execution == NOT_APPLIED
    assert out == data


def test_apply_italic_entire_run():
    data = _make_doc("machine learning")
    snapshot = read_document(data)
    f = _finding(
        _loc(snapshot, cs=0, ce=16), "machine learning", None,
        category=CATEGORY_ITALIC_FORMATTING,
    )
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_APPLY_ITALIC,
                              "replacement": None}}
    )
    engine.validate_plan(plan)
    out, plan = engine.apply_plan(plan)
    assert plan.items[0].execution == APPLIED
    doc2 = Document(io.BytesIO(out))
    assert doc2.paragraphs[0].runs[0].italic is True


def test_apply_italic_partial_splits_run():
    data = _make_doc("ini streaming video")
    snapshot = read_document(data)
    # "streaming" (4..13)
    f = _finding(
        _loc(snapshot, cs=4, ce=13), "streaming", None,
        category=CATEGORY_ITALIC_FORMATTING,
    )
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_APPLY_ITALIC,
                              "replacement": None}}
    )
    engine.validate_plan(plan)
    out, plan = engine.apply_plan(plan)
    assert plan.items[0].execution == APPLIED
    doc2 = Document(io.BytesIO(out))
    texts = [r.text for r in doc2.paragraphs[0].runs]
    itals = [r.italic for r in doc2.paragraphs[0].runs]
    assert "".join(texts) == "ini streaming video"
    # Tepat satu segmen (target) yang italic; segmen lain tidak italic.
    # "tidak italic" dapat berupa None (rPr asli tanpa <w:i>) atau False.
    # Mengubah None menjadi False akan merusak inheritance style,
    # jadi preservation yang benar mempertahankan None.
    assert itals.count(True) == 1
    target_idx = itals.index(True)
    for i, state in enumerate(itals):
        if i == target_idx:
            continue
        assert state is not True, (
            f"segmen {i} seharusnya tidak italic, bukan {state!r}"
        )


def test_complex_run_skipped():
    from docx.oxml import OxmlElement
    doc = Document()
    p = doc.add_paragraph()
    r = p.add_run("salah")
    br = OxmlElement("w:br")
    r._element.append(br)
    buf = io.BytesIO()
    doc.save(buf)
    data = buf.getvalue()
    snapshot = read_document(data)
    f = _finding(_loc(snapshot, cs=0, ce=5), "salah", "benar")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                              "replacement": "benar"}}
    )
    engine.validate_plan(plan)
    out, plan = engine.apply_plan(plan)
    assert plan.items[0].execution == SKIPPED
    assert plan.items[0].reason == "run_complex"


def test_snapshot_hash_mismatch():
    # Skenario: plan dibangun untuk satu dokumen, lalu divalidasi
    # terhadap engine yang memegang byte dokumen berbeda.
    data_a = _make_doc("Halo dunia")
    data_b = _make_doc("Dokumen lain sama sekali")
    snapshot = read_document(data_a)
    f = _finding(_loc(snapshot, cs=0, ce=4), "Halo", "Hai")

    engine_a = RepairEngine(data_a, snapshot)
    plan = engine_a.build_change_plan(
        [f], {f.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                              "replacement": "Hai"}}
    )

    engine_b = RepairEngine(data_b, snapshot)
    engine_b.validate_plan(plan)

    assert plan.items[0].validation == STALE
    assert plan.items[0].reason == "snapshot_hash_mismatch"
    # Tidak ada item valid yang bisa diterapkan.
    assert plan.valid_items() == []


def test_unknown_operation_unsupported():
    data = _make_doc("Halo dunia")
    snapshot = read_document(data)
    f = _finding(_loc(snapshot, cs=0, ce=4), "Halo", "Hai")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f], {f.finding_id: {"operation": "unknown_op",
                              "replacement": "x"}}
    )
    engine.validate_plan(plan)
    assert plan.items[0].validation == UNSUPPORTED


def test_multiple_edits_in_one_run_apply_descending():
    data = _make_doc("aaa bbb ccc")
    snapshot = read_document(data)
    # ganti "aaa" -> "xxx", "ccc" -> "yyy"
    f1 = _finding(_loc(snapshot, cs=0, ce=3), "aaa", "xxx")
    f2 = _finding(_loc(snapshot, cs=8, ce=11), "ccc", "yyy")
    engine = RepairEngine(data, snapshot)
    plan = engine.build_change_plan(
        [f1, f2],
        {
            f1.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                             "replacement": "xxx"},
            f2.finding_id: {"operation": OPERATION_REPLACE_TEXT,
                             "replacement": "yyy"},
        },
    )
    engine.validate_plan(plan)
    out, plan = engine.apply_plan(plan)
    for item in plan.items:
        assert item.execution == APPLIED
    doc2 = Document(io.BytesIO(out))
    assert doc2.paragraphs[0].text == "xxx bbb yyy"


def test_has_critical_failure_body():
    from src.docxlint.models.change_plan import ChangeItem, ChangePlan
    plan = ChangePlan(snapshot_id="x", snapshot_hash="y")
    plan.add(ChangeItem(
        change_id="c1", finding_id="f1",
        operation=OPERATION_REPLACE_TEXT,
        part="document", block_path="body/p[0]",
        run_index=0, char_start=0, char_end=3,
        original_value="abc", replacement="xyz",
        snapshot_hash="y",
        execution=FAILED,
    ))
    assert RepairEngine.has_critical_failure(plan) is True


def test_has_critical_failure_only_non_critical():
    from src.docxlint.models.change_plan import ChangeItem, ChangePlan
    plan = ChangePlan(snapshot_id="x", snapshot_hash="y")
    plan.add(ChangeItem(
        change_id="c1", finding_id="f1",
        operation=OPERATION_REPLACE_TEXT,
        part="document", block_path="body/p[0]",
        run_index=0, char_start=0, char_end=3,
        original_value="abc", replacement="xyz",
        snapshot_hash="y",
        execution=APPLIED,
    ))
    assert RepairEngine.has_critical_failure(plan) is False