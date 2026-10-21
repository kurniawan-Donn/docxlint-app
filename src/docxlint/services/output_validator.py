"""Validasi output DOCX setelah apply (Phase 6).

Tidak mengubah output. Hanya memverifikasi.
"""

from io import BytesIO
from typing import Iterable

from docx import Document

from ..models.change_plan import (
    APPLIED,
    ChangePlan,
    FAILED,
    ValidationReport,
)


def validate_output(
    output_bytes: bytes,
    plan: ChangePlan,
) -> ValidationReport:
    """Validasi output DOCX.

    - Reopen berhasil?
    - Komponen wajib ada? (dicek oleh validator Phase 2 di pemanggil)
    - Setiap item `applied` benar-benar terlihat di output?
    """
    if not output_bytes:
        return ValidationReport(ok=False, reason="empty_output")

    try:
        Document(BytesIO(output_bytes))
    except Exception as exc:
        return ValidationReport(
            ok=False,
            reason="reopen_failed",
            details={"error": type(exc).__name__},
        )

    from .docx_repair import _resolve_block

    doc = Document(BytesIO(output_bytes))
    failed = 0
    for item in plan.items:
        if item.execution != APPLIED:
            continue
        try:
            paragraph = _resolve_block(doc, item.block_path)
        except Exception:
            item.execution = FAILED
            item.reason = "post_validate_resolve_failed"
            failed += 1
            continue
        runs = paragraph.runs
        if item.run_index >= len(runs):
            item.execution = FAILED
            item.reason = "post_validate_run_missing"
            failed += 1
            continue
        if item.is_text_edit() and item.replacement:
            if item.replacement not in (runs[item.run_index].text or ""):
                item.execution = FAILED
                item.reason = "post_validate_text_missing"
                failed += 1

    if failed:
        return ValidationReport(
            ok=False, reason="post_validate_failures",
            details={"failed": failed},
        )
    return ValidationReport(ok=True, reason="ok")


__all__ = ["validate_output"]