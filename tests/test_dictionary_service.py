from pathlib import Path

from src.docxlint.services.dictionary_service import DictionaryService


def test_load_from_data():
    svc = DictionaryService.from_data(words=["makan", "rumah"])
    assert svc.status.loaded
    assert svc.status.word_count == 2


def test_is_known_case_insensitive():
    svc = DictionaryService.from_data(words=["makan"])
    assert svc.is_known("makan")
    assert svc.is_known("MAKAN")
    assert svc.is_known("Makan")
    assert not svc.is_known("makanan")


def test_whitelist_protected():
    svc = DictionaryService.from_data(words=["makan"], whitelist=["docx"])
    assert svc.is_protected("docx")
    assert svc.is_known("docx")


def test_exceptions_protected():
    svc = DictionaryService.from_data(
        words=["makan"], exceptions={"e-mail": "ejaan_baku"}
    )
    assert svc.is_protected("e-mail")


def test_terminology_protected():
    svc = DictionaryService.from_data(
        words=["makan"],
        terminology={"streaming": {"italic": True, "category": "x",
                                   "note": ""}},
    )
    assert svc.is_protected("streaming")


def test_lookup_root_morphology():
    svc = DictionaryService.from_data(words=["makan", "rumah"])
    assert svc.lookup_root("memakan") == "makan"
    assert svc.lookup_root("makanan") == "makan"
    assert svc.lookup_root("rumahnya") == "rumah"
    assert svc.lookup_root("bermain") is None


def test_missing_dictionary_graceful(tmp_path: Path):
    svc = DictionaryService(tmp_path)
    st = svc.load()
    assert not st.loaded
    assert st.error


def test_suggestions_deterministic():
    svc = DictionaryService.from_data(words=["makan", "makam", "malan"])
    s1 = svc.suggest("makan", max_n=3)
    s2 = svc.suggest("makan", max_n=3)
    assert s1 == s2


def test_suggestions_limit():
    svc = DictionaryService.from_data(
        words=["makan", "makam", "malan", "makin", "makna"]
    )
    s = svc.suggest("makn", max_n=3)
    assert len(s) <= 3


def test_suggestions_empty_when_no_match():
    svc = DictionaryService.from_data(words=["xyz"])
    assert svc.suggest("abcdefgh") == []


def test_duplicate_entries_handled(tmp_path: Path):
    path = tmp_path / "dictionary_id.txt"
    path.write_text("makan\nmakan\nrumah\n", encoding="utf-8")
    svc = DictionaryService(tmp_path)
    svc.load()
    assert svc.status.word_count == 2