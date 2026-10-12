"""Konfigurasi default DocxLint.

Angka di sini mengikuti DECISION-017 (FINAL):
- max file: 10 MB
- max uncompressed: 100 MB
- max ZIP entries: 2000
- max compression ratio: 100:1
- timeout: 60 s
- max findings: 5000
- confidence: 0.85 / 0.60 / 0.40
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    max_file_size_mb: int = 10
    max_uncompressed_mb: int = 100
    max_zip_entries: int = 2000
    max_compression_ratio: int = 100
    timeout_seconds: int = 60
    max_findings: int = 5000


@dataclass(frozen=True)
class ConfidenceThresholds:
    high: float = 0.85
    medium: float = 0.60
    low: float = 0.40


DEFAULT_LIMITS = Limits()
DEFAULT_CONFIDENCE = ConfidenceThresholds()

# Komponen minimum yang harus ada di paket DOCX
REQUIRED_DOCX_PARTS = ("[Content_Types].xml", "word/document.xml")

# Content type yang menandakan dokumen macro-enabled
MACRO_CONTENT_TYPES = (
    "application/vnd.ms-word.document.macroEnabled.main+xml",
    "application/vnd.ms-word.template.macroEnabledTemplate.main+xml",
)