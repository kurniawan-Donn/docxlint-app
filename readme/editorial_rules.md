# Editorial Rules — Italic untuk Istilah Asing

## Sumber
- Pedoman Umum Ejaan Bahasa Indonesia (PUEBI) — italic untuk kata/istilah asing.
- Konvensi editorial internal DocxLint (rekomendasi, bukan aturan universal).

## Prinsip
1. **Tidak semua kata Inggris harus italic.** Hanya istilah yang terdaftar di glossary.
2. **Glossary adalah sumber kebenaran.** Kolom `italic` menentukan ekspektasi.
3. **Nama produk, akronim, merek** biasanya tidak italic. Diatur lewat glossary dan `whitelist.txt`.
4. **Kata serapan umum** (mis. "email") tidak wajib italic.

## Rekomendasi vs Aturan
- Rekomendasi DocxLint: italic untuk istilah asing yang terdaftar.
- Aturan pengguna: ditentukan oleh isi `config/terminology.csv`.
- DocxLint tidak mengklaim kepatuhan terhadap standar editorial mana pun.

## Profil Editorial (config)
- `review_configured_foreign_terms`: laporkan setiap glossary match.
- `review_unlisted_foreign_candidates`: laporkan kandidat tak terdaftar (uncertain).
- `ignore_common_loanwords`, `ignore_acronyms`, `ignore_product_and_company_names`: heuristik suppress.
- `respect_existing_italic`: jika term sudah sesuai, tidak munculkan finding.
- `case_sensitive_terms`: profil global; per-term dapat override.

Default meminimalkan false positive: kandidat tak terdaftar **tidak** dilaporkan kecuali diaktifkan.