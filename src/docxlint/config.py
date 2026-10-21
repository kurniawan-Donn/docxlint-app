"""Konfigurasi default DocxLint.

DECISION-017 (FINAL):
- max file: 10 MB, max uncompressed: 100 MB, max ZIP entries: 2000
- max compression ratio: 100:1, timeout: 60 s, max findings: 5000
- confidence: 0.85 / 0.60 / 0.40

DECISION-027 (Phase 3): max_tokens: 200000 (ekstensi terbatas).
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
    max_tokens: int = 200_000  # DECISION-027


@dataclass(frozen=True)
class ConfidenceThresholds:
    high: float = 0.85
    medium: float = 0.60
    low: float = 0.40


DEFAULT_LIMITS = Limits()
DEFAULT_CONFIDENCE = ConfidenceThresholds()

@dataclass(frozen=True)
class ForeignTermPolicy:
    """Kebijakan Phase 4. Default meminimalkan false positive."""

    review_configured_foreign_terms: bool = True
    review_unlisted_foreign_candidates: bool = False
    ignore_common_loanwords: bool = True
    ignore_acronyms: bool = True
    ignore_product_and_company_names: bool = True
    respect_existing_italic: bool = True
    case_sensitive_terms: bool = False
    max_candidates_per_block: int = 200


DEFAULT_FOREIGN_POLICY = ForeignTermPolicy()

REQUIRED_DOCX_PARTS = ("[Content_Types].xml", "word/document.xml")

MACRO_CONTENT_TYPES = (
    "application/vnd.ms-word.document.macroEnabled.main+xml",
    "application/vnd.ms-word.template.macroEnabledTemplate.main+xml",
)

# Direktori konfigurasi default relatif terhadap root proyek.
# Restored for Phase 3 bugfix: app.py mengimpor nama ini.
CONFIG_DIR_NAME = "config"
PROFILES_DIR_NAME = "profiles"

DICTIONARY_FILE = "dictionary_id.txt"
WHITELIST_FILE = "whitelist.txt"
EXCEPTIONS_FILE = "exceptions.csv"
TERMINOLOGY_FILE = "terminology.csv"

# DECISION-025: token yang selalu diperlakukan sebagai "diketahui".
# Fail-safe agar istilah teknis umum tidak pernah muncul sebagai
# unknown_word walaupun dictionary/whitelist belum dikonfigurasi.
#
# Catatan: akronim umum (mis. "API") TIDAK dimasukkan ke sini agar
# Rule B (acronym detection) dapat mengklasifikasikannya sebagai
# unknown_word, sesuai test_acronym_unknown_not_typo. Untuk melindungi
# akronim di runtime, tambahkan ke config/whitelist.txt.
DEFAULT_PROTECTED_TERMS = frozenset({
    "docx", "streamlit", "python", "pytest", "lxml", "pip",
    "json", "yaml", "toml", "markdown", "csv", "pdf",
    "html", "xml", "url", "uri", "http", "https", "ftp",
    "uuid", "cli", "ui", "ux", "sdk",
})