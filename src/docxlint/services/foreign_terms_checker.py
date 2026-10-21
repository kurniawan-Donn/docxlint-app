"""Foreign terms checker Phase 4 — deteksi saja.

Keputusan FINAL yang dipatuhi:
- DECISION-007: Unknown != typo. Unknown juga != foreign.
- DECISION-008: Confidence 0.85 / 0.60 / 0.40.
- DECISION-009: Italic hanya dari terminology list.
- DECISION-017: max findings 5000 (dari Limits).
- DECISION-021: Run kompleks -> skipped.
- DECISION-025: Protected terms suppress total.

Tidak ada auto-italic. Tidak ada modifikasi DOCX.
"""

import re
from typing import List, Optional

from ..config import (
    DEFAULT_FOREIGN_POLICY,
    DEFAULT_LIMITS,
    ForeignTermPolicy,
    Limits,
)
from ..models.document import Block, DocumentSnapshot, Location
from ..models.finding import (
    APPLICATION_NOT_APPLIED,
    CATEGORY_FOREIGN_TERM,
    CATEGORY_ITALIC_FORMATTING,
    Finding,
    ITALIC_FULLY,
    ITALIC_NOT,
    ITALIC_PARTIALLY,
    ITALIC_SKIPPED,
    ITALIC_UNKNOWN,
    RULE_FOREIGN_CANDIDATE,
    RULE_FOREIGN_CONFIGURED,
    RULE_ITALIC_MISMATCH,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    make_finding_id,
)
from .dictionary_service import DictionaryService
from .glossary_service import GlossaryMatch, GlossaryService
from .italic_inspector import inspect_italic


_ACRONYM_RE = re.compile(r"^[A-Z][A-Z0-9]{1,7}$")
# Token finder di dalam teks bebas. TANPA anchor ^...$ karena dipakai
# dengan finditer() pada blok yang bisa berisi spasi/tanda baca.
# Boundary Unicode-aware: hindari match di dalam kata lain.
_ASCII_WORD_RE = re.compile(r"(?<![A-Za-z])[A-Za-z]{4,}(?![A-Za-z])")


class ForeignTermsChecker:
    def __init__(
        self,
        glossary: GlossaryService,
        dictionary: DictionaryService,
        policy: Optional[ForeignTermPolicy] = None,
        limits: Optional[Limits] = None,
    ) -> None:
        self.glossary = glossary
        self.dictionary = dictionary
        self.policy = policy or DEFAULT_FOREIGN_POLICY
        self.limits = limits or DEFAULT_LIMITS
        self.tokens_scanned: int = 0
        self.matches_seen: int = 0

    def check(self, snapshot: DocumentSnapshot) -> List[Finding]:
        findings: List[Finding] = []
        self.tokens_scanned = 0
        self.matches_seen = 0

        if not self.glossary.status.loaded:
            return findings

        for block in snapshot.all_blocks():
            if not block.text.strip():
                continue
            matches = self.glossary.find_matches(block.text)
            self.matches_seen += len(matches)

            if self.policy.review_configured_foreign_terms:
                for m in matches:
                    findings.append(self._make_configured_finding(m, block, snapshot))
                    if len(findings) >= self.limits.max_findings:
                        return findings

            for m in matches:
                italic_finding = self._make_italic_finding(m, block, snapshot)
                if italic_finding is not None:
                    findings.append(italic_finding)
                    if len(findings) >= self.limits.max_findings:
                        return findings

            if self.policy.review_unlisted_foreign_candidates:
                candidates = self._find_candidates(block, matches)
                for token_text, cs, ce in candidates:
                    f = self._make_candidate_finding(
                        token_text, cs, ce, block, snapshot,
                    )
                    if f is not None:
                        findings.append(f)
                        if len(findings) >= self.limits.max_findings:
                            return findings

        return findings

    # --- builders ------------------------------------------------------

    def _make_configured_finding(
        self, m: GlossaryMatch, block: Block, snapshot: DocumentSnapshot,
    ) -> Finding:
        italic_state, _reason = inspect_italic(
            block, m.char_start, m.char_end,
        )
        expected_italic = m.entry.italic
        return Finding(
            finding_id=make_finding_id(),
            rule_id=RULE_FOREIGN_CONFIGURED,
            category=CATEGORY_FOREIGN_TERM,
            severity=SEVERITY_INFO,
            location=_locate(snapshot, block, m.char_start, m.char_end),
            original_value=m.matched_text,
            suggested_value=None,
            reason=(
                f"Istilah terdaftar di glossary "
                f"(kategori: {m.entry.category or 'umum'})."
            ),
            confidence=0.95,
            review_status="pending",
            application_status=APPLICATION_NOT_APPLIED,
            metadata={
                "glossary_term": m.entry.term,
                "language": m.entry.language,
                "expected_italic": expected_italic,
                "observed_italic_state": italic_state,
                "match_type": "configured",
                "note": m.entry.note,
                "match_global_start": m.char_start,
                "match_global_end": m.char_end,
            },
        )

    def _make_italic_finding(
        self, m: GlossaryMatch, block: Block, snapshot: DocumentSnapshot,
    ) -> Optional[Finding]:
        state, reason = inspect_italic(block, m.char_start, m.char_end)
        if state == ITALIC_SKIPPED:
            return Finding(
                finding_id=make_finding_id(),
                rule_id=RULE_ITALIC_MISMATCH,
                category=CATEGORY_ITALIC_FORMATTING,
                severity=SEVERITY_INFO,
                location=_locate(snapshot, block, m.char_start, m.char_end),
                original_value=m.matched_text,
                suggested_value=None,
                reason="Run kompleks; status italic tidak dapat ditentukan.",
                confidence=0.30,
                application_status="skipped",
                metadata={
                    "observed_italic_state": state,
                    "reason": reason,
                    "match_type": "configured",
                },
            )
        expected = m.entry.italic
        if state == ITALIC_UNKNOWN:
            if not self.policy.respect_existing_italic:
                return None
            return Finding(
                finding_id=make_finding_id(),
                rule_id=RULE_ITALIC_MISMATCH,
                category=CATEGORY_ITALIC_FORMATTING,
                severity=SEVERITY_INFO,
                location=_locate(snapshot, block, m.char_start, m.char_end),
                original_value=m.matched_text,
                suggested_value=None,
                reason="Status italic tidak dapat ditentukan (style inheritance).",
                confidence=0.40,
                metadata={
                    "observed_italic_state": state,
                    "expected_italic": expected,
                    "match_type": "configured",
                },
            )
        # Mismatch check
        is_ok = (
            (expected and state == ITALIC_FULLY)
            or (not expected and state == ITALIC_NOT)
        )
        if is_ok and self.policy.respect_existing_italic:
            return None
        if is_ok:
            return None

        if expected and state == ITALIC_NOT:
            severity = SEVERITY_MEDIUM
            confidence = 0.90
            reason = "Istilah asing terdaftar seharusnya italic, tetapi tidak italic."
            suggested = "italic"
        elif expected and state == ITALIC_PARTIALLY:
            severity = SEVERITY_LOW
            confidence = 0.75
            reason = "Istilah asing terdaftar hanya sebagian italic."
            suggested = "italic"
        elif (not expected) and state == ITALIC_FULLY:
            severity = SEVERITY_LOW
            confidence = 0.75
            reason = "Istilah terdaftar tidak seharusnya italic, tetapi italic."
            suggested = "non_italic"
        else:
            return None

        return Finding(
            finding_id=make_finding_id(),
            rule_id=RULE_ITALIC_MISMATCH,
            category=CATEGORY_ITALIC_FORMATTING,
            severity=severity,
            location=_locate(snapshot, block, m.char_start, m.char_end),
            original_value=m.matched_text,
            suggested_value=suggested,
            reason=reason,
            confidence=confidence,
            metadata={
                "observed_italic_state": state,
                "expected_italic": expected,
                "match_type": "configured",
                "glossary_term": m.entry.term,
            },
        )

    def _find_candidates(
        self,
        block: Block,
        matches: List[GlossaryMatch],
    ) -> List[tuple]:
        """Kandidat konservatif: ASCII-letter, panjang >=4, bukan protected,
        bukan di kamus, bukan bagian dari glossary match."""
        if not self.dictionary.status.loaded:
            return []
        covered = [(m.char_start, m.char_end) for m in matches]
        candidates: List[tuple] = []
        for r in block.runs:
            if r.is_complex_run:
                continue
            for m in _ASCII_WORD_RE.finditer(r.text):
                token = m.group(0)
                gs = r.char_start + m.start()
                ge = r.char_start + m.end()
                if any(gs < c_end and c_start < ge for c_start, c_end in covered):
                    continue
                low = token.lower()
                if _ACRONYM_RE.match(token):
                    if self.policy.ignore_acronyms:
                        continue
                if self.dictionary.is_protected(low):
                    continue
                if self.dictionary.is_known(low):
                    continue
                if self.dictionary.lookup_root(low):
                    continue
                candidates.append((token, gs, ge))
                if len(candidates) >= self.policy.max_candidates_per_block:
                    break
        return candidates

    def _make_candidate_finding(
        self,
        token_text: str,
        char_start: int,
        char_end: int,
        block: Block,
        snapshot: DocumentSnapshot,
    ) -> Optional[Finding]:
        state, _ = inspect_italic(block, char_start, char_end)
        return Finding(
            finding_id=make_finding_id(),
            rule_id=RULE_FOREIGN_CANDIDATE,
            category=CATEGORY_FOREIGN_TERM,
            severity=SEVERITY_INFO,
            location=_locate(snapshot, block, char_start, char_end),
            original_value=token_text,
            suggested_value=None,
            reason=(
                "Kandidat istilah asing (uncertain). Tidak ada di kamus "
                "Indonesia maupun glossary. Perlu verifikasi manual."
            ),
            confidence=0.30,
            metadata={
                "match_type": "candidate",
                "observed_italic_state": state,
                "uncertain": True,
            },
        )


def _locate(
    snapshot: DocumentSnapshot,
    block: Block,
    global_start: int,
    global_end: int,
) -> Location:
    """Petakan offset global blok ke run_index + offset dalam run.

    Jika rentang menyeberangi beberapa run, pakai run pertama dan
    clip char_end ke batas run pertama. Rentang lengkap tetap dicatat
    di metadata finding.
    """
    first_run = None
    for r in block.runs:
        if r.char_end <= global_start or r.char_start >= global_end:
            continue
        first_run = r
        break
    if first_run is None:
        # Fallback: run 0, offset 0
        return Location(
            snapshot_id=snapshot.snapshot_id,
            part=block.part,
            block_path=block.block_path,
            block_type=block.block_type,
            run_index=0,
            char_start=0,
            char_end=0,
            global_text_offset=global_start,
        )
    local_start = max(global_start, first_run.char_start) - first_run.char_start
    local_end = min(global_end, first_run.char_end) - first_run.char_start
    return Location(
        snapshot_id=snapshot.snapshot_id,
        part=block.part,
        block_path=block.block_path,
        block_type=block.block_type,
        run_index=first_run.run_index,
        char_start=local_start,
        char_end=local_end,
        global_text_offset=global_start,
    )


__all__ = ["ForeignTermsChecker"]