"""Language checker Phase 3 — deteksi saja.

Tidak mengubah DOCX. Tidak ada edit. Tidak ada AI generatif.

Keputusan FINAL yang dipatuhi:
- DECISION-007: Unknown != typo.
- DECISION-008: Confidence 0.85 / 0.60 / 0.40.
- DECISION-017: max findings 5000 (dari Limits).
- DECISION-021: Run kompleks -> skipped (tokenisasi dilewati).
- DECISION-027: max_tokens 200000.
"""

import re
from typing import List, Optional

from ..config import DEFAULT_LIMITS, Limits
from ..models.document import Block, DocumentSnapshot, Location, Run
from ..models.finding import (
    APPLICATION_SKIPPED,
    CATEGORY_SPELLING,
    CATEGORY_UNKNOWN_WORD,
    Finding,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    make_finding_id,
)
from .dictionary_service import DictionaryService
from .tokenizer import Token, tokenize


_ACRONYM_RE = re.compile(r"^[A-Z][A-Z0-9]{1,7}$")


class LanguageChecker:
    def __init__(
        self,
        dictionary: DictionaryService,
        limits: Optional[Limits] = None,
    ) -> None:
        self.dictionary = dictionary
        self.limits = limits or DEFAULT_LIMITS
        # Statistik sesi
        self.tokens_scanned: int = 0
        self.skipped_complex_runs: int = 0

    def check(self, snapshot: DocumentSnapshot) -> List[Finding]:
        findings: List[Finding] = []
        self.tokens_scanned = 0
        self.skipped_complex_runs = 0

        if not self.dictionary.status.loaded:
            return findings

        for block in snapshot.all_blocks():
            for run in block.runs:
                if run.is_complex_run:
                    # DECISION-021: jangan tokenisasi run kompleks.
                    self.skipped_complex_runs += 1
                    continue
                if not run.text:
                    continue
                for token in tokenize(run.text):
                    self.tokens_scanned += 1
                    if self.tokens_scanned > self.limits.max_tokens:
                        return findings
                    finding = self._check_token(token, block, run, snapshot)
                    if finding is not None:
                        findings.append(finding)
                        if len(findings) >= self.limits.max_findings:
                            return findings
        return findings

    # --- per token -----------------------------------------------------

    def _check_token(
        self,
        token: Token,
        block: Block,
        run: Run,
        snapshot: DocumentSnapshot,
    ) -> Optional[Finding]:

        # 1. Protected (whitelist/exception/terminology)
        if self.dictionary.is_protected(token.normalized):
            return None

        # 2. Kamus langsung
        if self.dictionary.is_known(token.normalized):
            return None

        # 3. Morfologi
        if self.dictionary.lookup_root(token.normalized):
            return None

        # 4. Akronim / singkatan -> unknown, bukan typo
        if _ACRONYM_RE.match(token.text):
            return self._build_unknown(
                token, block, run, snapshot,
                reason="Akronim atau singkatan; tidak diperiksa sebagai typo.",
            )

        # 5. Terlalu pendek
        if len(token.text) < 2:
            return None

        # 6. Cari saran
        suggestions = self.dictionary.suggest(token.normalized, max_n=3)
        if suggestions:
            best_word, best_dist = suggestions[0]
            confidence = _confidence_from_distance(
                best_dist, len(token.text))
            if confidence >= 0.60:
                severity = (
                    SEVERITY_HIGH if confidence >= 0.85 else SEVERITY_MEDIUM
                )
                return Finding(
                    finding_id=make_finding_id(),
                    rule_id="SPELL_001",
                    category=CATEGORY_SPELLING,
                    severity=severity,
                    location=_locate(snapshot, block, run, token),
                    original_value=token.text,
                    suggested_value=best_word,
                    reason=(
                        "Kata mirip dengan kata di kamus; kemungkinan "
                        "salah eja."
                    ),
                    confidence=confidence,
                    metadata={
                        "suggestions": [s[0] for s in suggestions],
                        "distances": [s[1] for s in suggestions],
                    },
                )

        # 7. Unknown word
        return self._build_unknown(
            token, block, run, snapshot,
            reason="Kata tidak ditemukan di kamus lokal.",
        )

    def _build_unknown(
        self,
        token: Token,
        block: Block,
        run: Run,
        snapshot: DocumentSnapshot,
        reason: str,
    ) -> Finding:
        return Finding(
            finding_id=make_finding_id(),
            rule_id="UNKNOWN_001",
            category=CATEGORY_UNKNOWN_WORD,
            severity=SEVERITY_INFO,
            location=_locate(snapshot, block, run, token),
            original_value=token.text,
            suggested_value=None,
            reason=reason,
            confidence=0.30,
            metadata={"run_complex": run.is_complex_run},
        )


def _locate(
    snapshot: DocumentSnapshot,
    block: Block,
    run: Run,
    token: Token,
) -> Location:
    return Location(
        snapshot_id=snapshot.snapshot_id,
        part=block.part,
        block_path=block.block_path,
        block_type=block.block_type,
        run_index=run.run_index,
        char_start=token.char_start,
        char_end=token.char_end,
    )


def _confidence_from_distance(distance: int, length: int) -> float:
    if distance == 1:
        return 0.90
    if distance == 2:
        return 0.70 if length >= 5 else 0.55
    if distance == 3:
        return 0.40
    return 0.30


__all__ = ["LanguageChecker"]