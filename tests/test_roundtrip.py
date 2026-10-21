import io
import zipfile

from src.docxlint.services.docx_reader import read_document
from src.docxlint.services.docx_writer import export_roundtrip


def test_roundtrip_preserves_paragraphs(minimal_docx_bytes):
    exported = export_roundtrip(minimal_docx_bytes)
    snapshot = read_document(exported)
    assert any(b.text == "Halo dunia" for b in snapshot.parts["document"])


def test_roundtrip_preserves_table(docx_with_table_bytes):
    exported = export_roundtrip(docx_with_table_bytes)
    texts = [b.text for b in read_document(exported).parts["document"]]
    for expected in ("A1", "B1", "A2", "B2"):
        assert expected in texts


def test_roundtrip_required_components(minimal_docx_bytes):
    exported = export_roundtrip(minimal_docx_bytes)
    with zipfile.ZipFile(io.BytesIO(exported)) as zf:
        names = set(zf.namelist())
    assert "[Content_Types].xml" in names
    assert "word/document.xml" in names


def test_roundtrip_byte_for_byte_identical(minimal_docx_bytes):
    assert export_roundtrip(minimal_docx_bytes) == minimal_docx_bytes