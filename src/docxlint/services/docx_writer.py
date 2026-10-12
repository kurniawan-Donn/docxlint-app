"""Writer DOCX — Phase 2: hanya round-trip.

Tidak ada edit di Phase 2. Tidak ada apply_finding, replace_run_text,
atau split run. Fase selanjutnya akan menambah fungsi edit selektif.
"""

from io import BytesIO

from docx import Document


def save_original_bytes(data: bytes) -> bytes:
    """Kembalikan bytes DOCX asli tanpa perubahan."""
    return data


def export_roundtrip(data: bytes) -> bytes:
    """Ekspor no-op. Phase 2: identik dengan bytes asli."""
    return save_original_bytes(data)


def load_from_bytes(data: bytes) -> Document:
    """Muat Document dari bytes. Untuk pemakaian read-only di Phase 2."""
    return Document(BytesIO(data))


__all__ = ["save_original_bytes", "export_roundtrip", "load_from_bytes"]