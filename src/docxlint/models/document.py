"""Model data inti DocxLint. Mengikuti docs/data_model.md."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class Run:
    run_index: int
    text: str
    char_start: int
    char_end: int
    is_complex_run: bool
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    xml_element: Any = None


@dataclass
class Block:
    block_path: str
    block_type: str
    part: str
    text: str
    runs: List[Run] = field(default_factory=list)
    style_name: Optional[str] = None
    numbering: Optional[Dict[str, Any]] = None
    xml_element: Any = None


@dataclass
class DocumentSnapshot:
    snapshot_id: str
    parts: Dict[str, List[Block]] = field(default_factory=dict)

    def all_blocks(self) -> Iterator[Block]:
        for blocks in self.parts.values():
            yield from blocks


@dataclass
class Location:
    """Lokasi temuan. Sesuai docs/data_model.md."""

    snapshot_id: str
    part: str
    block_path: str
    block_type: str
    run_index: int
    char_start: int
    char_end: int
    section_index: Optional[int] = None
    global_text_offset: Optional[int] = None
    original_text_hash: Optional[str] = None