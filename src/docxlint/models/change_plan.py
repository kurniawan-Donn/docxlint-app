"""Model change plan Phase 6.

Tidak mengubah dokumen. Hanya mendeskripsikan perubahan yang diusulkan.
"""

from dataclasses import dataclass, field
from typing import List, Optional


OPERATION_REPLACE_TEXT = "replace_text"
OPERATION_APPLY_ITALIC = "apply_italic"

# Validation status (sebelum eksekusi)
VALID = "valid"
STALE = "stale"
CONFLICT = "conflict"
UNSUPPORTED = "unsupported"
REJECTED = "rejected"

# Execution status (setelah eksekusi)
NOT_APPLIED = "not_applied"
APPLIED = "applied"
SKIPPED = "skipped"
FAILED = "failed"


@dataclass
class ChangeItem:
    change_id: str
    finding_id: str
    operation: str                     # OPERATION_REPLACE_TEXT | OPERATION_APPLY_ITALIC
    part: str
    block_path: str
    run_index: int
    char_start: int
    char_end: int
    original_value: str
    replacement: Optional[str]         # None untuk apply_italic
    snapshot_hash: str
    validation: str = VALID
    execution: str = NOT_APPLIED
    reason: str = ""
    global_text_offset: Optional[int] = None

    def is_text_edit(self) -> bool:
        return self.operation == OPERATION_REPLACE_TEXT

    def is_italic_edit(self) -> bool:
        return self.operation == OPERATION_APPLY_ITALIC


@dataclass
class ChangePlan:
    snapshot_id: str
    snapshot_hash: str
    items: List[ChangeItem] = field(default_factory=list)
    profile_id: str = ""              # extension Phase 7
    profile_version: str = ""         # extension Phase 7
    config_hash: str = ""             # extension Phase 7

    def add(self, item: ChangeItem) -> None:
        self.items.append(item)

    def valid_items(self) -> List[ChangeItem]:
        return [i for i in self.items if i.validation == VALID]

    def rejected_items(self) -> List[ChangeItem]:
        return [i for i in self.items if i.validation != VALID]

    def counts(self) -> dict:
        c = {
            "planned": len(self.items),
            "valid": 0,
            "stale": 0,
            "conflict": 0,
            "unsupported": 0,
            "rejected": 0,
            "applied": 0,
            "skipped": 0,
            "failed": 0,
            "not_applied": 0,
        }
        for i in self.items:
            c[i.validation] = c.get(i.validation, 0) + 1
            if i.execution in c:
                c[i.execution] += 1
        return c


@dataclass
class ValidationReport:
    ok: bool
    reason: str = ""
    details: dict = field(default_factory=dict)


__all__ = [
    "ChangeItem", "ChangePlan", "ValidationReport",
    "OPERATION_REPLACE_TEXT", "OPERATION_APPLY_ITALIC",
    "VALID", "STALE", "CONFLICT", "UNSUPPORTED", "REJECTED",
    "NOT_APPLIED", "APPLIED", "SKIPPED", "FAILED",
]