"""Model profil formatting Phase 7."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


PROFILE_SCHEMA_VERSION = 1


@dataclass
class FormattingRule:
    rule_id: str
    enabled: bool
    severity: str = "medium"
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormattingProfile:
    profile_id: str
    name: str
    description: str
    version: str
    schema_version: int
    rules: Dict[str, FormattingRule] = field(default_factory=dict)
    editorial_policy: Optional[Dict[str, Any]] = None
    notes: str = ""
    source: str = "builtin"

    def enabled_rules(self) -> List[FormattingRule]:
        return [r for r in self.rules.values() if r.enabled]

    def get_rule(self, rule_id: str) -> Optional[FormattingRule]:
        return self.rules.get(rule_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "source": self.source,
            "editorial_policy": dict(self.editorial_policy or {}),
            "notes": self.notes,
            "rules": {
                rid: {
                    "enabled": r.enabled,
                    "severity": r.severity,
                    "params": dict(r.params),
                }
                for rid, r in self.rules.items()
            },
        }


__all__ = ["FormattingProfile", "FormattingRule", "PROFILE_SCHEMA_VERSION"]