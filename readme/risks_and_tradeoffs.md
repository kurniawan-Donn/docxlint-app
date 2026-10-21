docs/risks_and_tradeoffs.md
1. Risiko Utama
Risiko	Dampak	Mitigasi
Preservasi format tidak sempurna	Pengguna kecewa	Batasi klaim, uji format, tandai fitur tidak didukung.
False positive ejaan	Review berlebihan	Kamus konservatif, confidence, status unknown.
Run terpecah	Sulit edit	Pemetaan offset, split run, atau tandai manual.
Lisensi KBBI	Legal	Jangan redistribusi tanpa izin; gunakan sumber berlisensi jelas.
Demo publik tidak privat	Kebocoran data	Peringatan jelas, batas file, cleanup, hanya non-sensitif.
Resource exhaustion	Server demo down	Batas ukuran, timeout, validasi ZIP.
Fitur Word kompleks	Data hilang	Deteksi, peringatan, jangan hapus diam-diam.
2. Trade-off
Konservatif vs agresif: konservatif mengurangi false positive tetapi menambah review manual.

Local-first vs demo: local lebih aman, demo lebih mudah diakses.

python-docx vs manipulasi XML langsung: python-docx lebih aman, tetapi terbatas.

Aturan berbasis kamus vs AI: MVP tanpa AI lebih deterministik dan privat.

3. MVP Exclusions
AI generatif.

Database.

Autentikasi.

Microservices.

KBBI penuh.

Tracked changes, comments, footnotes, text boxes, equations.

Jaminan preservasi semua fitur Word.
# Risks & Tradeoffs (Phase 1.5 Update)

## Risiko Baru
- Network guard false positive.
- Rollback memori besar.
- Overlap kompleks.

## Mitigasi
- Whitelist localhost.
- Batas memori.
- Manual review.