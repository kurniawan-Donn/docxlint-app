import io

from docx import Document

from src.docxlint.models.document import (
    Block, DocumentSnapshot, Run,
)
from src.docxlint.services.dictionary_service import DictionaryService
from src.docxlint.services.language_checker import LanguageChecker


def _snapshot_from_paragraphs(texts):
    blocks = []
    for i, text in enumerate(texts):
        run = Run(
            run_index=0, text=text,
            char_start=0, char_end=len(text),
            is_complex_run=False,
        )
        blocks.append(
            Block(
                block_path=f"body/p[{i}]",
                block_type="paragraph",
                part="document",
                text=text,
                runs=[run],
            )
        )
    return DocumentSnapshot(snapshot_id="snap-1",
                            parts={"document": blocks})


def _dict(words=("makan", "rumah", "buku", "salah", "halo", "dunia",
                 "komputer", "kata", "ejaan")):
    return DictionaryService.from_data(words=words)


def test_detect_likely_misspelling():
    svc = _dict()
    snapshot = _snapshot_from_paragraphs(["salahh ejaan"])
    findings = LanguageChecker(svc).check(snapshot)
    assert any(
        f.original_value == "salahh" and f.category == "spelling"
        for f in findings
    )


def test_correct_word_not_flagged():
    svc = _dict()
    snapshot = _snapshot_from_paragraphs(["makan rumah buku"])
    findings = LanguageChecker(svc).check(snapshot)
    assert findings == []


def test_unknown_technical_term():
    svc = _dict()
    snapshot = _snapshot_from_paragraphs(["kubernetes cluster"])
    findings = LanguageChecker(svc).check(snapshot)
    assert any(
        f.original_value == "kubernetes"
        and f.category == "unknown_word"
        for f in findings
    )


def test_acronym_unknown_not_typo():
    svc = _dict()
    snapshot = _snapshot_from_paragraphs(["API endpoint"])
    findings = LanguageChecker(svc).check(snapshot)
    api_finding = next(
        (f for f in findings if f.original_value == "API"), None
    )
    assert api_finding is not None
    assert api_finding.category == "unknown_word"


def test_repeated_occurrences_distinct_locations():
    svc = _dict()
    snapshot = _snapshot_from_paragraphs(["salahh", "salahh"])
    findings = LanguageChecker(svc).check(snapshot)
    spell_findings = [f for f in findings if f.original_value == "salahh"]
    assert len(spell_findings) == 2
    assert len({f.finding_id for f in spell_findings}) == 2
    assert spell_findings[0].location.block_path != \
        spell_findings[1].location.block_path


def test_protected_terms_not_flagged():
    svc = _dict()
    snapshot = _snapshot_from_paragraphs(["docx streamlit"])
    findings = LanguageChecker(svc).check(snapshot)
    assert findings == []


def test_no_auto_modification():
    svc = _dict()
    snapshot = _snapshot_from_paragraphs(["salahh"])
    original_text = snapshot.parts["document"][0].text
    LanguageChecker(svc).check(snapshot)
    assert snapshot.parts["document"][0].text == original_text


def test_complex_run_skipped():
    svc = _dict()
    complex_run = Run(
        run_index=0, text="salahh",
        char_start=0, char_end=6,
        is_complex_run=True,
    )
    block = Block(
        block_path="body/p[0]", block_type="paragraph",
        part="document", text="salahh", runs=[complex_run],
    )
    snapshot = DocumentSnapshot(
        snapshot_id="x", parts={"document": [block]}
    )
    checker = LanguageChecker(svc)
    findings = checker.check(snapshot)
    assert findings == []
    assert checker.skipped_complex_runs == 1


def test_max_findings_respected():
    from src.docxlint.config import Limits
    limits = Limits(max_findings=2)
    svc = _dict(words=("xyz",))
    snapshot = _snapshot_from_paragraphs(
        ["abcdefg", "hijklmn", "opqrstu"]
    )
    findings = LanguageChecker(svc, limits=limits).check(snapshot)
    assert len(findings) <= 2


def test_dictionary_missing_returns_no_findings(tmp_path):
    svc = DictionaryService(tmp_path)
    svc.load()
    snapshot = _snapshot_from_paragraphs(["salahh"])
    assert LanguageChecker(svc).check(snapshot) == []