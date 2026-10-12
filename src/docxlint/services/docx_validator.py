"""Validasi file DOCX sebelum diproses.

Defensive check: menolak file yang jelas tidak layak diproses.
Tidak menjamin mendeteksi semua file berbahaya.
"""

import io
import zipfile
from pathlib import Path
from typing import Optional

from ..config import (
    DEFAULT_LIMITS,
    Limits,
    MACRO_CONTENT_TYPES,
    REQUIRED_DOCX_PARTS,
)
from ..utils.errors import (
    FileTooLargeError,
    InvalidDocxError,
    UnsupportedFileTypeError,
    ValidationError,
)


class DocxValidator:
    """Validator paket DOCX berbasis ZIP."""

    def __init__(self, limits: Optional[Limits] = None) -> None:
        self.limits = limits or DEFAULT_LIMITS

    def validate(self, data: bytes, filename: str) -> None:
        """Validasi menyeluruh. Raise ValidationError jika gagal."""
        self._check_filename(filename)
        self._check_size(data)
        self._check_zip(data)
        self._check_components(data)
        self._check_macros(data)

    # ---- langkah-langkah -------------------------------------------------

    def _check_filename(self, filename: str) -> None:
        suffix = Path(filename).suffix.lower()
        if suffix == ".docm":
            raise UnsupportedFileTypeError(
                "File .docm (macro-enabled) tidak didukung."
            )
        if suffix != ".docx":
            raise UnsupportedFileTypeError("Hanya file .docx yang didukung.")

    def _check_size(self, data: bytes) -> None:
        if not data:
            raise ValidationError("File kosong.")
        limit = self.limits.max_file_size_mb * 1024 * 1024
        if len(data) > limit:
            raise FileTooLargeError(
                f"Ukuran file melebihi batas {self.limits.max_file_size_mb} MB."
            )

    def _check_zip(self, data: bytes) -> None:
        if not data.startswith(b"PK\x03\x04"):
            raise InvalidDocxError("File bukan arsip ZIP/DOCX yang valid.")
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                infos = zf.infolist()
                if len(infos) > self.limits.max_zip_entries:
                    raise InvalidDocxError(
                        "Jumlah entri ZIP melebihi batas aman."
                    )
                total_uncompressed = 0
                for info in infos:
                    total_uncompressed += info.file_size
                    if info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > self.limits.max_compression_ratio:
                            raise InvalidDocxError(
                                "Rasio kompresi ZIP mencurigakan."
                            )
                    name = info.filename.replace("\\", "/")
                    parts = name.split("/")
                    if name.startswith("/") or ".." in parts:
                        raise InvalidDocxError(
                            "Entri ZIP dengan path tidak aman."
                        )
                limit_uncompressed = (
                    self.limits.max_uncompressed_mb * 1024 * 1024
                )
                if total_uncompressed > limit_uncompressed:
                    raise InvalidDocxError(
                        "Ukuran tidak terkompresi melebihi batas."
                    )
        except zipfile.BadZipFile as exc:
            raise InvalidDocxError("Arsip ZIP rusak.") from exc

    def _check_components(self, data: bytes) -> None:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = set(zf.namelist())
        except zipfile.BadZipFile as exc:
            raise InvalidDocxError("Arsip ZIP rusak.") from exc
        for required in REQUIRED_DOCX_PARTS:
            if required not in names:
                raise InvalidDocxError(
                    f"Komponen DOCX wajib tidak ditemukan: {required}"
                )

    def _check_macros(self, data: bytes) -> None:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = set(zf.namelist())
                if "word/vbaProject.bin" in names:
                    raise UnsupportedFileTypeError(
                        "File berisi makro (vbaProject.bin). Ditolak."
                    )
                try:
                    content_types = zf.read("[Content_Types].xml").decode(
                        "utf-8", errors="ignore"
                    )
                except KeyError:
                    return
        except zipfile.BadZipFile as exc:
            raise InvalidDocxError("Arsip ZIP rusak.") from exc
        for macro_type in MACRO_CONTENT_TYPES:
            if macro_type in content_types:
                raise UnsupportedFileTypeError(
                    "Content type macro-enabled tidak didukung."
                )