import pytest

from src.docxlint.config import ForeignTermPolicy
from src.docxlint.models.document import Block, DocumentSnapshot, Run
from src.docxlint.services.dictionary_service import DictionaryService
from src.docxlint.services.foreign_terms_checker import (
    ForeignTermsChecker,
)
from src.docxlint.services.glossary_service import GlossaryService


def _snapshot(text, italic=False):
    run = Run(
        run_index=0, text=text,
        char_start=0, char_end=len(text),
        is_complex_run=False, italic=italic,
    )
    blk = Block(
        block_path="body/p[0]", block_type="paragraph",
        part="document", text=text, runs=[run],
    )
    return DocumentSnapshot(snapshot_id="x", parts={"document": [blk]})


def _dict():
    return DictionaryService.from_data(words=("adalah", "modern", "video"))


def _glossary():
    return GlossaryService.from_data([
        {"term": "machine learning", "italic": True, "category": "istilah_asing"},
        {"term": "streaming", "italic": True, "category": "istilah_asing"},
    ])


def test_configured_match_detected():
    checker = ForeignTermsChecker(_glossary(), _dict())
    findings = checker.check(_snapshot("topik machine learning modern"))
    rules = {f.rule_id for f in findings}
    assert "FOREIGN_001" in rules


def test_italic_mismatch_when_not_italic():
    checker = ForeignTermsChecker(_glossary(), _dict())
    findings = checker.check(_snapshot("machine learning", italic=False))
    italic = [f for f in findings if f.rule_id == "ITALIC_001"]
    assert italic
    assert italic[0].metadata["observed_italic_state"] == "not_italicized"


def test_italic_ok_when_already_italic():
    checker = ForeignTermsChecker(_glossary(), _dict())
    findings = checker.check(_snapshot("machine learning", italic=True))
    italic = [f for f in findings if f.rule_id == "ITALIC_001"]
    assert italic == []


def test_unknown_words_not_foreign_by_default():
    policy = ForeignTermPolicy(review_unlisted_foreign_candidates=False)
    checker = ForeignTermsChecker(_glossary(), _dict(), policy=policy)
    findings = checker.check(_snapshot("kubernetes cluster"))
    assert all(f.rule_id != "FOREIGN_002" for f in findings)


def test_candidates_when_enabled():
    policy = ForeignTermPolicy(review_unlisted_foreign_candidates=True)
    checker = ForeignTermsChecker(_glossary(), _dict(), policy=policy)
    findings = checker.check(_snapshot("kubernetes cluster"))
    candidates = [f for f in findings if f.rule_id == "FOREIGN_002"]
    assert candidates
    assert all(f.metadata.get("uncertain") for f in candidates)


def test_acronym_excluded_from_candidates():
    policy = ForeignTermPolicy(review_unlisted_foreign_candidates=True)
    checker = ForeignTermsChecker(_glossary(), _dict(), policy=policy)
    findings = checker.check(_snapshot("API endpoint"))
    candidates = [f for f in findings if f.rule_id == "FOREIGN_002"]
    texts = {f.original_value for f in candidates}
    assert "API" not in texts


def test_repeated_occurrences_distinct_locations():
    checker = ForeignTermsChecker(_glossary(), _dict())
    findings = checker.check(_snapshot("streaming lalu streaming"))
    matches = [f for f in findings if f.rule_id == "FOREIGN_001"]
    assert len(matches) == 2
    assert len({f.finding_id for f in matches}) == 2


def test_glossary_missing_returns_empty(tmp_path):
    g = GlossaryService(tmp_path)
    g.load()
    checker = ForeignTermsChecker(g, _dict())
    assert checker.check(_snapshot("machine learning")) == []


def test_no_docx_modification():
    snapshot = _snapshot("machine learning", italic=False)
    original = snapshot.parts["document"][0].text
    ForeignTermsChecker(_glossary(), _dict()).check(snapshot)
    assert snapshot.parts["document"][0].text == original