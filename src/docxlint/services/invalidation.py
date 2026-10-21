"""Invalidasi findings dan change plan berdasarkan profile/config."""

from typing import Iterable, List, Tuple

from ..models.change_plan import ChangePlan
from ..models.finding import Finding


def is_finding_stale(
    finding: Finding,
    current_profile_id: str,
    current_config_hash: str,
) -> bool:
    meta = finding.metadata or {}
    if meta.get("profile_id") and \
            meta["profile_id"] != current_profile_id:
        return True
    if meta.get("config_hash") and \
            meta["config_hash"] != current_config_hash:
        return True
    return False


def mark_stale_findings(
    findings: Iterable[Finding],
    current_profile_id: str,
    current_config_hash: str,
) -> List[Finding]:
    out: List[Finding] = []
    for f in findings:
        if is_finding_stale(f, current_profile_id, current_config_hash):
            f.application_status = "stale"
            f.reason = (f.reason or "") + " [stale: profile/config berubah]"
        out.append(f)
    return out


def is_change_plan_valid(
    plan: ChangePlan,
    current_profile_id: str,
    current_config_hash: str,
) -> Tuple[bool, str]:
    if plan.profile_id and plan.profile_id != current_profile_id:
        return False, "profile_changed"
    if plan.config_hash and plan.config_hash != current_config_hash:
        return False, "config_changed"
    return True, ""


__all__ = [
    "is_change_plan_valid",
    "is_finding_stale",
    "mark_stale_findings",
]