from src.docxlint.services.tokenizer import tokenize


def test_basic_tokenization():
    toks = tokenize("Halo dunia")
    assert [t.text for t in toks] == ["Halo", "dunia"]
    assert toks[0].char_start == 0 and toks[0].char_end == 4
    assert toks[1].char_start == 5 and toks[1].char_end == 10


def test_punctuation_not_tokens():
    toks = tokenize("ya, apa? oke!")
    assert [t.text for t in toks] == ["ya", "apa", "oke"]


def test_case_preserved_and_normalized():
    toks = tokenize("Halo HALO halo")
    assert [t.text for t in toks] == ["Halo", "HALO", "halo"]
    assert all(t.normalized == "halo" for t in toks)


def test_hyphenated_token_kept_together():
    toks = tokenize("kata-kata indah")
    assert toks[0].text == "kata-kata"
    assert toks[1].text == "indah"


def test_apostrophe_inside_word():
    toks = tokenize("nggak'kan gitu")
    assert toks[0].text == "nggak'kan"
    assert toks[1].text == "gitu"


def test_unicode_word():
    toks = tokenize("café naïve")
    assert [t.text for t in toks] == ["café", "naïve"]


def test_numbers_and_dates_skipped():
    toks = tokenize("Tanggal 2024-01-01 dan 3.14 pi")
    assert "2024" not in [t.text for t in toks]
    assert "01" not in [t.text for t in toks]
    assert "3.14" not in [t.text for t in toks]
    assert "pi" in [t.text for t in toks]


def test_urls_emails_paths_skipped():
    text = "Kunjungi https://contoh.com atau kirim ke a@b.com, cek C:\\tmp\\file.txt"
    tokens = [t.text for t in tokenize(text)]
    assert "https" not in tokens
    assert "contoh" not in tokens
    assert "b" not in tokens
    assert "tmp" not in tokens
    assert "Kunjungi" in tokens
    assert "kirim" in tokens


def test_offsets_accurate_for_unicode():
    text = "café dunia"
    toks = tokenize(text)
    assert text[toks[0].char_start:toks[0].char_end] == "café"
    assert text[toks[1].char_start:toks[1].char_end] == "dunia"


def test_no_tokens_for_empty():
    assert tokenize("") == []
    assert tokenize("   ,,, ...") == []