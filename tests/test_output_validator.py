import io

from docx import Document

from src.docxlint.models.change_plan import (
    APPLIED, ChangeItem, ChangePlan, FAILED,
)
from src.docxlint.services.docx_reader import read_document
from src.docxlint.services.docx_repair import RepairEngine
from src.docxlint.services.output_validator import validate_output


def _doc():
    d = Document()
    d.add_paragraph("Halo dunia")
    b = io.BytesIO()
    d.save(b)
    return b.getvalue()


def test_validate_ok():
    data = _doc()
    snapshot = read_document(data)
    engine = RepairEngine(data, snapshot)
    plan = ChangePlan(snapshot_id=snapshot.snapshot_id,
                       snapshot_hash=engine.snapshot_hash)
    plan.add(ChangeItem(
        change_id="c1", finding_id="f1", operation="replace_text",
        part="document", block_path="body/p[0]",
        run_index=0, char_start=0, char_end=4,
        original_value="Halo", replacement="Hai",
        snapshot_hash=engine.snapshot_hash,
    ))
    out, plan = engine.apply_plan(plan)
    report = validate_output(out, plan)
    assert report.ok is True


def test_validate_empty():
    report = validate_output(b"", ChangePlan(snapshot_id="x", snapshot_hash="y"))
    assert report.ok is False
    assert report.reason == "empty_output"


def test_validate_invalid_bytes():
    report = validate_output(b"not a docx",
                             ChangePlan(snapshot_id="x", snapshot_hash="y"))
    assert report.ok is False