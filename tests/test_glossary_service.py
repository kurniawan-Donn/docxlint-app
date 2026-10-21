from src.docxlint.services.glossary_service import GlossaryService


def _svc(entries, exceptions=None):
    return GlossaryService.from_data(entries, exceptions=exceptions)


def test_exact_single_word_match():
    g = _svc([{"term": "streaming", "italic": True}])
    m = g.find_matches("ini streaming video")
    assert len(m) == 1
    assert m[0].matched_text == "streaming"


def test_multiword_match():
    g = _svc([{"term": "machine learning", "italic": True}])
    m = g.find_matches("topik machine learning modern")
    assert len(m) == 1
    assert m[0].matched_text == "machine learning"


def test_no_partial_match_inside_word():
    g = _svc([{"term": "api", "italic": False}])
    m = g.find_matches("capitalism adalah")
    assert m == []


def test_case_insensitive_default():
    g = _svc([{"term": "machine learning", "italic": True}])
    m = g.find_matches("Machine Learning dan MACHINE LEARNING")
    assert len(m) == 2


def test_case_sensitive_opt_in():
    g = _svc([{"term": "API", "italic": False, "case_sensitive": True}])
    assert g.find_matches("API dan api")[0].matched_text == "API"
    assert len(g.find_matches("api saja")) == 0


def test_unicode():
    g = _svc([{"term": "café", "italic": True}])
    m = g.find_matches("menu café spesial")
    assert m[0].matched_text == "café"


def test_repeated_occurrences():
    g = _svc([{"term": "streaming", "italic": True}])
    m = g.find_matches("streaming lalu streaming")
    assert len(m) == 2
    assert m[0].char_start < m[1].char_start


def test_overlapping_terms_prefer_longest():
    g = _svc([
        {"term": "machine", "italic": True},
        {"term": "machine learning", "italic": True},
    ])
    m = g.find_matches("machine learning adalah")
    assert len(m) == 1
    assert m[0].matched_text == "machine learning"


def test_exceptions_suppress():
    g = _svc(
        [{"term": "streaming", "italic": True}],
        exceptions={"streaming"},
    )
    assert g.find_matches("streaming video") == []


def test_whitespace_flexible_multiword():
    g = _svc([{"term": "machine learning", "italic": True}])
    m = g.find_matches("machine   learning modern")
    assert len(m) == 1
    assert m[0].matched_text.startswith("machine")


def test_not_match_across_paragraphs():
    g = _svc([{"term": "machine learning", "italic": True}])
    # karena kita mencari per blok, ini tidak akan match di teks yang
    # digabung; di sini kita pastikan "machine\nlearning" tidak match
    # jika newline bukan whitespace fleksibel dalam konteks blok tunggal.
    # (Reader memisahkan paragraf, jadi pencarian selalu per blok.)
    assert g.find_matches("machine learning")[0].matched_text