from src.docxlint.services.docx_writer import (
    export_roundtrip,
    load_from_bytes,
    save_original_bytes,
)


def test_save_original_bytes_identical(minimal_docx_bytes):
    assert save_original_bytes(minimal_docx_bytes) == minimal_docx_bytes


def test_export_roundtrip_identical(minimal_docx_bytes):
    assert export_roundtrip(minimal_docx_bytes) == minimal_docx_bytes


def test_load_from_bytes(minimal_docx_bytes):
    doc = load_from_bytes(minimal_docx_bytes)
    texts = [p.text for p in doc.paragraphs]
    assert "Halo dunia" in texts