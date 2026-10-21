"""Model Finding. Mengikuti docs/data_model.md."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .document import Location


CATEGORY_SPELLING = "spelling"
CATEGORY_UNKNOWN_WORD = "unknown_word"

CATEGORY_FOREIGN_TERM = "foreign_term"
CATEGORY_ITALIC_FORMATTING = "italic_formatting"

# Observed italic state (Phase 4)
ITALIC_FULLY = "fully_italicized"
ITALIC_PARTIALLY = "partially_italicized"
ITALIC_NOT = "not_italicized"
ITALIC_UNKNOWN = "unknown"
ITALIC_SKIPPED = "skipped"

# Rule IDs Phase 4
RULE_FOREIGN_CONFIGURED = "FOREIGN_001"
RULE_FOREIGN_CANDIDATE = "FOREIGN_002"
RULE_ITALIC_MISMATCH = "ITALIC_001"

# Reserved untuk fase berikutnya:
# punctuation, repeated_word, foreign_italic, formatting

SEVERITY_INFO = "info"
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

REVIEW_PENDING = "pending"
REVIEW_ACCEPTED = "accepted"
REVIEW_REJECTED = "rejected"
REVIEW_CONFLICT = "conflict"

APPLICATION_NOT_APPLIED = "not_applied"
APPLICATION_APPLIED = "applied"
APPLICATION_FAILED = "failed"
APPLICATION_SKIPPED = "skipped"
APPLICATION_STALE = "stale"
APPLICATION_CONFLICT = "conflict"


def make_finding_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Finding:
    finding_id: str
    rule_id: str
    category: str
    severity: str
    location: Location
    original_value: str
    suggested_value: Optional[str]
    reason: str
    confidence: float
    review_status: str = REVIEW_PENDING
    application_status: str = APPLICATION_NOT_APPLIED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "location": {
                "snapshot_id": self.location.snapshot_id,
                "part": self.location.part,
                "block_path": self.location.block_path,
                "block_type": self.location.block_type,
                "run_index": self.location.run_index,
                "char_start": self.location.char_start,
                "char_end": self.location.char_end,
            },
            "original_value": self.original_value,
            "suggested_value": self.suggested_value,
            "reason": self.reason,
            "confidence": self.confidence,
            "review_status": self.review_status,
            "application_status": self.application_status,
            "metadata": dict(self.metadata),
        }