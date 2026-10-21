import io
import zipfile

import pytest

from src.docxlint.config import Limits
from src.docxlint.services.docx_validator import DocxValidator
from src.docxlint.utils.errors import (
    FileTooLargeError,
    InvalidDocxError,
    UnsupportedFileTypeError,
    ValidationError,
)


def test_valid_minimal_docx(minimal_docx_bytes):
    DocxValidator().validate(minimal_docx_bytes, "test.docx")


def test_wrong_extension(minimal_docx_bytes):
    with pytest.raises(UnsupportedFileTypeError):
        DocxValidator().validate(minimal_docx_bytes, "test.txt")


def test_empty_upload():
    with pytest.raises(ValidationError):
        DocxValidator().validate(b"", "empty.docx")


def test_invalid_zip():
    with pytest.raises(InvalidDocxError):
        DocxValidator().validate(b"not a zip file", "bad.docx")


def test_missing_required_components():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("random.txt", "hello")
    with pytest.raises(InvalidDocxError):
        DocxValidator().validate(buf.getvalue(), "broken.docx")


def test_file_too_large():
    small_limits = Limits(max_file_size_mb=1)
    data = b"PK\x03\x04" + b"x" * (2 * 1024 * 1024)
    with pytest.raises(FileTooLargeError):
        DocxValidator(small_limits).validate(data, "big.docx")


def test_too_many_entries():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<document/>")
        for i in range(10):
            zf.writestr(f"extra/{i}.txt", "x")
    small_limits = Limits(max_zip_entries=5)
    with pytest.raises(InvalidDocxError):
        DocxValidator(small_limits).validate(buf.getvalue(), "many.docx")


def test_docm_rejection(minimal_docx_bytes):
    with pytest.raises(UnsupportedFileTypeError):
        DocxValidator().validate(minimal_docx_bytes, "macro.docm")


def test_path_traversal_rejected():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<document/>")
        zf.writestr("../../evil.txt", "x")
    with pytest.raises(InvalidDocxError):
        DocxValidator().validate(buf.getvalue(), "trav.docx")