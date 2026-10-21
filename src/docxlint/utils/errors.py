"""Exception kustom DocxLint.

Semua pesan error yang muncul ke pengguna TIDAK boleh memuat isi dokumen.
"""


class DocxLintError(Exception):
    """Base error DocxLint."""


class ValidationError(DocxLintError):
    """Validasi file gagal (umum)."""


class UnsupportedFileTypeError(ValidationError):
    """Tipe file tidak didukung (mis. .docm, .txt)."""


class FileTooLargeError(ValidationError):
    """File melebihi batas ukuran."""


class InvalidDocxError(ValidationError):
    """Paket DOCX/ZIP tidak valid atau rusak."""


class LocalModeNetworkBlocked(DocxLintError):
    """Koneksi keluar diblokir di mode lokal."""