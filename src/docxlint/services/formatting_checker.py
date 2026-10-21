"""Formatting checker Phase 7. Detection only.

Mengikuti DECISION-021 (run kompleks -> skipped) dan DECISION-008
(confidence threshold). Tidak mengubah dokumen.
"""

import re
from typing import Iterable, List, Optional

from ..config import DEFAULT_LIMITS, Limits
from ..models.document import Block, DocumentSnapshot, Location, Run
from ..models.finding import (
    Finding,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    make_finding_id,
)
from ..models.profile import FormattingProfile


_RULE_TO_CATEGORY = {
    "FMT_FONT_FAMILY": "formatting",
    "FMT_FONT_SIZE": "formatting",
    "FMT_ALIGNMENT": "formatting",
    "FMT_LINE_SPACING": "formatting",
    "FMT_PARAGRAPH_SPACING": "formatting",
    "FMT_INDENT": "formatting",
    "FMT_MARGIN": "formatting",
}

_SEVERITY_MAP = {
    "info": SEVERITY_INFO,
    "low": SEVERITY_LOW,
    "medium": SEVERITY_MEDIUM,
    "high": SEVERITY_HIGH,
}


class FormattingChecker:
    def __init__(
        self,
        profile: FormattingProfile,
        limits: Optional[Limits] = None,
    ) -> None:
        self.profile = profile
        self.limits = limits or DEFAULT_LIMITS
        self.blocks_scanned: int = 0
        self.runs_scanned: int = 0

    def check(self, snapshot: DocumentSnapshot) -> List[Finding]:
        findings: List[Finding] = []
        self.blocks_scanned = 0
        self.runs_scanned = 0
        for rule in self.profile.enabled_rules():
            handler = getattr(self, f"_check_{rule.rule_id.lower()}",
                              None)
            if handler is None:
                continue
            for block in snapshot.all_blocks():
                self.blocks_scanned += 1
                result = handler(rule, block, snapshot)
                if result:
                    findings.extend(result)
                    if len(findings) >= self.limits.max_findings:
                        return findings
        return findings

    # --- rule handlers -------------------------------------------------

    def _check_fmt_font_family(self, rule, block, snapshot):
        allowed = _normalize_allowed(rule.params.get("allowed"))
        if not allowed:
            return []
        out: List[Finding] = []
        for run in block.runs:
            if run.is_complex_run:
                out.append(_skipped(rule, block, run, snapshot,
                                     "run_complex"))
                continue
            self.runs_scanned += 1
            name = _run_font_name(run)
            if name is None:
                continue  # inherited; jangan false positive
            if name.lower() not in allowed:
                out.append(_make_finding(
                    rule, block, run, snapshot,
                    reason=f"Font '{name}' tidak diizinkan.",
                    suggested=", ".join(sorted(allowed)),
                    confidence=0.75,
                ))
        return out

    def _check_fmt_font_size(self, rule, block, snapshot):
        allowed = _normalize_allowed_pt(rule.params.get("allowed_pt"))
        if not allowed:
            return []
        out: List[Finding] = []
        for run in block.runs:
            if run.is_complex_run:
                out.append(_skipped(rule, block, run, snapshot,
                                     "run_complex"))
                continue
            size_pt = _run_font_size_pt(run)
            if size_pt is None:
                continue
            rounded = round(size_pt)
            if rounded not in allowed:
                out.append(_make_finding(
                    rule, block, run, snapshot,
                    reason=f"Ukuran font {size_pt:.1f}pt tidak diizinkan.",
                    suggested=f"{sorted(allowed)}",
                    confidence=0.75,
                ))
        return out

    def _check_fmt_alignment(self, rule, block, snapshot):
        allowed = _normalize_allowed(rule.params.get("allowed"))
        if not allowed:
            return []
        value = _block_alignment(block)
        if value is None:
            return []
        if value not in allowed:
            return [_make_block_finding(
                rule, block, snapshot,
                reason=f"Alignment '{value}' tidak diizinkan.",
                suggested=", ".join(sorted(allowed)),
                confidence=0.70,
            )]
        return []

    def _check_fmt_line_spacing(self, rule, block, snapshot):
        allowed = _normalize_allowed_float(rule.params.get("allowed"))
        if not allowed:
            return []
        value = _block_line_spacing(block)
        if value is None:
            return []
        if round(value, 2) not in allowed:
            return [_make_block_finding(
                rule, block, snapshot,
                reason=f"Line spacing {value} tidak diizinkan.",
                suggested=f"{sorted(allowed)}",
                confidence=0.70,
            )]
        return []

    def _check_fmt_paragraph_spacing(self, rule, block, snapshot):
        """params: max_before_pt, max_after_pt"""
        max_before = rule.params.get("max_before_pt")
        max_after = rule.params.get("max_after_pt")
        before = _block_space_before_pt(block)
        after = _block_space_after_pt(block)
        if before is None and after is None:
            return []
        issues = []
        if isinstance(max_before, (int, float)) and before is not None \
                and before > max_before:
            issues.append(f"space_before={before}pt > {max_before}pt")
        if isinstance(max_after, (int, float)) and after is not None \
                and after > max_after:
            issues.append(f"space_after={after}pt > {max_after}pt")
        if not issues:
            return []
        return [_make_block_finding(
            rule, block, snapshot,
            reason="; ".join(issues),
            suggested=f"before<={max_before}, after<={max_after}",
            confidence=0.70,
        )]

    def _check_fmt_indent(self, rule, block, snapshot):
        """params: first_line_cm, left_cm, right_cm (opsional)."""
        expected_first = rule.params.get("first_line_cm")
        expected_left = rule.params.get("left_cm")
        expected_right = rule.params.get("right_cm")
        actual_first = _block_first_line_indent_cm(block)
        actual_left = _block_left_indent_cm(block)
        actual_right = _block_right_indent_cm(block)
        issues = []
        if isinstance(expected_first, (int, float)) \
                and actual_first is not None \
                and abs(actual_first - expected_first) > 0.05:
            issues.append(f"first_line={actual_first}cm, harap {expected_first}cm")
        if isinstance(expected_left, (int, float)) \
                and actual_left is not None \
                and abs(actual_left - expected_left) > 0.05:
            issues.append(f"left={actual_left}cm, harap {expected_left}cm")
        if isinstance(expected_right, (int, float)) \
                and actual_right is not None \
                and abs(actual_right - expected_right) > 0.05:
            issues.append(f"right={actual_right}cm, harap {expected_right}cm")
        if not issues:
            return []
        return [_make_block_finding(
            rule, block, snapshot,
            reason="; ".join(issues),
            suggested="sesuaikan indentasi",
            confidence=0.70,
        )]


# --- helper ekstraksi properti --------------------------------------------

def _run_font_name(run: Run) -> Optional[str]:
    # Reader Phase 2 tidak menyimpan font.name; ambil dari XML.
    try:
        rpr = run._element.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr"
        )
        if rpr is None:
            return None
        rfonts = rpr.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts"
        )
        if rfonts is None:
            return None
        for attr in (
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii",
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi",
        ):
            v = rfonts.get(attr)
            if v:
                return v
    except Exception:
        return None
    return None


def _run_font_size_pt(run: Run) -> Optional[float]:
    try:
        rpr = run._element.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr"
        )
        if rpr is None:
            return None
        sz = rpr.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz"
        )
        if sz is None:
            return None
        val = sz.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
        )
        if val is None:
            return None
        return int(val) / 2.0  # half-points -> pt
    except Exception:
        return None


def _block_alignment(block: Block) -> Optional[str]:
    try:
        ppr = block._element.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
        )
        if ppr is None:
            return None
        jc = ppr.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc"
        )
        if jc is None:
            return None
        return jc.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
        )
    except Exception:
        return None


def _block_line_spacing(block: Block) -> Optional[float]:
    try:
        ppr = block._element.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
        )
        if ppr is None:
            return None
        sp = ppr.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing"
        )
        if sp is None:
            return None
        line = sp.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line"
        )
        line_rule = sp.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lineRule"
        )
        if line is None:
            return None
        val = int(line)
        if line_rule == "auto":
            return val / 240.0
        return val / 20.0
    except Exception:
        return None


def _block_space_before_pt(block: Block) -> Optional[float]:
    return _block_spacing_attr_pt(block, "before")


def _block_space_after_pt(block: Block) -> Optional[float]:
    return _block_spacing_attr_pt(block, "after")


def _block_spacing_attr_pt(block: Block, attr: str) -> Optional[float]:
    try:
        ppr = block._element.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
        )
        if ppr is None:
            return None
        sp = ppr.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing"
        )
        if sp is None:
            return None
        val = sp.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            + attr
        )
        if val is None:
            return None
        return int(val) / 20.0
    except Exception:
        return None


def _block_first_line_indent_cm(block: Block) -> Optional[float]:
    return _block_indent_cm(block, "firstLine")


def _block_left_indent_cm(block: Block) -> Optional[float]:
    return _block_indent_cm(block, "left")


def _block_right_indent_cm(block: Block) -> Optional[float]:
    return _block_indent_cm(block, "right")


def _block_indent_cm(block: Block, attr: str) -> Optional[float]:
    try:
        ppr = block._element.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
        )
        if ppr is None:
            return None
        ind = ppr.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ind"
        )
        if ind is None:
            return None
        val = ind.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            + attr
        )
        if val is None:
            return None
        return int(val) / 567.0  # twips -> cm approx (1 cm ~ 567 twips)
    except Exception:
        return None


def _normalize_allowed(raw) -> List[str]:
    if not isinstance(raw, list):
        return []
    return [str(x).strip().lower() for x in raw if str(x).strip()]


def _normalize_allowed_pt(raw) -> List[int]:
    if not isinstance(raw, list):
        return []
    out = []
    for x in raw:
        try:
            out.append(int(round(float(x))))
        except (TypeError, ValueError):
            continue
    return out


def _normalize_allowed_float(raw) -> List[float]:
    if not isinstance(raw, list):
        return []
    out = []
    for x in raw:
        try:
            out.append(round(float(x), 2))
        except (TypeError, ValueError):
            continue
    return out


# --- finding builders -----------------------------------------------------

def _make_finding(rule, block, run, snapshot, reason, suggested,
                  confidence):
    return Finding(
        finding_id=make_finding_id(),
        rule_id=rule.rule_id,
        category=_RULE_TO_CATEGORY.get(rule.rule_id, "formatting"),
        severity=_SEVERITY_MAP.get(rule.severity, SEVERITY_MEDIUM),
        location=_locate_run(snapshot, block, run),
        original_value=run.text,
        suggested_value=suggested,
        reason=reason,
        confidence=confidence,
        metadata={
            "profile_id": _profile_id(rule),
            "rule_params": dict(rule.params),
        },
    )


def _make_block_finding(rule, block, snapshot, reason, suggested,
                        confidence):
    return Finding(
        finding_id=make_finding_id(),
        rule_id=rule.rule_id,
        category=_RULE_TO_CATEGORY.get(rule.rule_id, "formatting"),
        severity=_SEVERITY_MAP.get(rule.severity, SEVERITY_MEDIUM),
        location=Location(
            snapshot_id=snapshot.snapshot_id,
            part=block.part,
            block_path=block.block_path,
            block_type=block.block_type,
            run_index=0,
            char_start=0,
            char_end=0,
        ),
        original_value=block.text[:80],
        suggested_value=suggested,
        reason=reason,
        confidence=confidence,
        metadata={"rule_params": dict(rule.params)},
    )


def _skipped(rule, block, run, snapshot, reason):
    return Finding(
        finding_id=make_finding_id(),
        rule_id=rule.rule_id,
        category=_RULE_TO_CATEGORY.get(rule.rule_id, "formatting"),
        severity=SEVERITY_INFO,
        location=_locate_run(snapshot, block, run),
        original_value=run.text,
        suggested_value=None,
        reason=reason,
        confidence=0.30,
        application_status="skipped",
        metadata={"rule_params": dict(rule.params)},
    )


def _locate_run(snapshot, block, run):
    return Location(
        snapshot_id=snapshot.snapshot_id,
        part=block.part,
        block_path=block.block_path,
        block_type=block.block_type,
        run_index=run.run_index,
        char_start=run.char_start,
        char_end=run.char_end,
    )


def _profile_id(rule) -> str:
    return getattr(rule, "profile_id", "")


__all__ = ["FormattingChecker"]