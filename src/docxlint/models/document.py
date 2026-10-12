"""Model data inti DocxLint.

Mengikuti docs/data_model.md. Tidak menambah nama field baru.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class Run:
    """Satu run teks dalam sebuah paragraf.

    `char_start`/`char_end` adalah offset terhadap teks gabungan paragraf,
    bukan offset absolut dokumen.
    """

    run_index: int
    text: str
    char_start: int
    char_end: int
    is_complex_run: bool
    bold: Optional[bool] = None
    italic: Optional[bool] = None


@dataclass
class Block:
    """Blok logis: paragraf, heading, list item, atau paragraf dalam sel tabel."""

    block_path: str
    block_type: str  # paragraph | heading | list_item | hyperlink
    part: str        # document | header[N] | footer[N]
    text: str
    runs: List[Run] = field(default_factory=list)
    style_name: Optional[str] = None
    numbering: Optional[Dict[str, Any]] = None


@dataclass
class DocumentSnapshot:
    """Hasil pembacaan dokumen pada satu titik waktu.

    `parts` memetakan nama bagian (mis. "document", "header[0]")
    ke daftar Block.
    """

    snapshot_id: str
    parts: Dict[str, List[Block]] = field(default_factory=dict)

    def all_blocks(self) -> Iterator[Block]:
        for blocks in self.parts.values():
            yield from blocks


@dataclass
class Location:
    """Lokasi temuan. Belum dipakai di Phase 2, disiapkan untuk Phase 3+."""

    snapshot_id: str
    part: str
    block_path: str
    block_type: str
    run_index: int
    char_start: int
    char_end: int
    original_text_hash: Optional[str] = None