"""Load, validate, dan pilih formatting profile Phase 7."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from ..models.profile import (
    PROFILE_SCHEMA_VERSION,
    FormattingProfile,
    FormattingRule,
)


KNOWN_RULE_IDS = {
    "FMT_FONT_FAMILY",
    "FMT_FONT_SIZE",
    "FMT_ALIGNMENT",
    "FMT_LINE_SPACING",
    "FMT_PARAGRAPH_SPACING",
    "FMT_INDENT",
    "FMT_MARGIN",
}

KNOWN_SEVERITIES = {"info", "low", "medium", "high"}


@dataclass
class ProfileValidationReport:
    ok: bool
    errors: List[str] = field(default_factory=list)


def _parse_rule(rule_id: str, raw: dict) -> Tuple[
    Optional[FormattingRule], List[str]
]:
    errors: List[str] = []
    if not isinstance(raw, dict):
        return None, [f"RULE_{rule_id}_NOT_MAPPING"]
    enabled = bool(raw.get("enabled", True))
    severity = str(raw.get("severity", "medium")).lower()
    if severity not in KNOWN_SEVERITIES:
        errors.append(f"RULE_{rule_id}_SEVERITY_UNKNOWN: {severity}")
        severity = "medium"
    params = raw.get("params") or {}
    if not isinstance(params, dict):
        errors.append(f"RULE_{rule_id}_PARAMS_NOT_MAPPING")
        params = {}
    return (
        FormattingRule(
            rule_id=rule_id, enabled=enabled,
            severity=severity, params=dict(params),
        ),
        errors,
    )


def validate_profile(profile: FormattingProfile) -> ProfileValidationReport:
    errors: List[str] = []
    if not profile.profile_id:
        errors.append("PROFILE_MISSING_ID")
    if profile.schema_version != PROFILE_SCHEMA_VERSION:
        errors.append(f"PROFILE_SCHEMA_UNSUPPORTED: {profile.schema_version}")
    if not profile.version:
        errors.append("PROFILE_MISSING_VERSION")
    for rid, rule in profile.rules.items():
        if rid not in KNOWN_RULE_IDS:
            errors.append(f"RULE_UNKNOWN: {rid}")
        if rule.severity not in KNOWN_SEVERITIES:
            errors.append(f"RULE_SEVERITY_UNKNOWN: {rid}")
    return ProfileValidationReport(ok=not errors, errors=errors)


def _load_yaml(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML tidak tersedia.")
    with path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
    if not isinstance(loaded, dict):
        raise ValueError(f"profile bukan mapping: {path.name}")
    return loaded


def profile_from_dict(data: dict, source: str = "user") -> FormattingProfile:
    rules: Dict[str, FormattingRule] = {}
    raw_rules = data.get("rules") or {}
    if not isinstance(raw_rules, dict):
        raw_rules = {}
    for rid, raw in raw_rules.items():
        rule, _ = _parse_rule(rid, raw)
        if rule is not None:
            rules[rid] = rule
    return FormattingProfile(
        profile_id=str(data.get("profile_id") or ""),
        name=str(data.get("name") or data.get("profile_id") or ""),
        description=str(data.get("description") or ""),
        version=str(data.get("version") or "0.0.0"),
        schema_version=int(data.get("schema_version")
                           or PROFILE_SCHEMA_VERSION),
        rules=rules,
        editorial_policy=data.get("editorial_policy") or None,
        notes=str(data.get("notes") or ""),
        source=source,
    )


def load_profile_from_path(path: Path) -> FormattingProfile:
    data = _load_yaml(path)
    return profile_from_dict(data, source="builtin")


def load_builtin_profiles(directory: Path) -> List[FormattingProfile]:
    if not directory.exists():
        return []
    out: List[FormattingProfile] = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            out.append(load_profile_from_path(path))
        except Exception:
            continue
    return out


class ProfileRegistry:
    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self._profiles: Dict[str, FormattingProfile] = {}
        self._loaded = False

    def load(self) -> None:
        self._profiles = {}
        for p in load_builtin_profiles(self.directory):
            self._profiles[p.profile_id] = p
        self._loaded = True

    def list(self) -> List[FormattingProfile]:
        return list(self._profiles.values())

    def get(self, profile_id: str) -> Optional[FormattingProfile]:
        return self._profiles.get(profile_id)


__all__ = [
    "KNOWN_RULE_IDS",
    "ProfileRegistry",
    "ProfileValidationReport",
    "load_builtin_profiles",
    "load_profile_from_path",
    "profile_from_dict",
    "validate_profile",
]