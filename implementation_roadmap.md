docs/implementation_roadmap.md
Fase	Fokus	Hasil
Phase 2	Fondasi: model, config, reader	Baca DOCX dan indeks lokasi.
Phase 3	Rule engine dasar	Ejaan, tanda baca, kata berulang, italic.
Phase 4	Writer selektif	Terapkan temuan, stale check, overlap.
Phase 5	Formatting rules	Cek dan perbaikan format aman.
Phase 6	Streamlit UI	Upload, review, apply, unduh.
Phase 7	Hardening	Security, privacy, testing, malformed.
Phase 8	Demo & portofolio	Deploy demo publik, dokumentasi, polish.
Unresolved Decisions
Keputusan	Default Rekomendasi	Dampak
Sumber kamus	Daftar terkurasi + sumber berlisensi jelas	Menghindari masalah hukum.
Batas file demo	10 MB	Mencegah resource exhaustion.
Cakupan fitur Word	Daftar MVP eksplisit	Menghindari klaim berlebihan.
Threshold confidence	Konservatif	Mengurangi false positive.
Penyimpanan data	File JSON/CSV, bukan database	Sederhana untuk satu developer.
Phase 1 Completion Report
Dokumen yang Diusulkan
docs/requirements.md

docs/architecture.md

docs/data_model.md

docs/security_privacy.md

docs/testing_strategy.md

docs/risks_and_tradeoffs.md

docs/implementation_roadmap.md

Keputusan yang Sudah Diambil
Python + Streamlit.

Local-first, tanpa AI generatif.

Satu DOCX per sesi.

Review sebelum apply.

python-docx sebagai basis, dengan catatan limitasi.

Tidak ada database, autentikasi, atau microservices.

Demo publik hanya untuk dokumen non-sensitif.

KBBI hanya referensi; tidak ada asumsi redistribusi bebas.

Pertanyaan yang Belum Terselesaikan
Sumber kamus/istilah final dan lisensinya.

Batas ukuran file demo final.

Daftar fitur Word yang didukung penuh vs hanya diperingatkan.

Threshold severity dan confidence final.

Risiko Utama
Preservasi format tidak sempurna.

False positive ejaan.

Kompleksitas run dan XML.

Privasi demo publik.

Lisensi data kamus.

Acceptance Test yang Diusulkan
File malformed ditolak dengan pesan jelas.

Tidak ada panggilan jaringan di mode lokal.

Temuan memiliki ID, rule, lokasi, dan status.

Perubahan teks sederhana mempertahankan format run.

Fitur tidak didukung ditandai, bukan dihapus.

File sementara demo dibersihkan.

# Roadmap (Phase 1.5 Update)

| Fase | Fokus | Output |
|---|---|---|
| Phase 2 | Model, config, reader, network guard | Fondasi |
| Phase 3 | Rule engine dasar | Ejaan, tanda baca, kata berulang |
| Phase 4 | Writer selektif + validasi + rollback | Apply aman |
| Phase 5 | Formatting rules | Cek & perbaikan |
| Phase 6 | Streamlit UI + diff preview | UX |
| Phase 7 | Hardening + testing | Kualitas |
| Phase 8 | Demo + dokumentasi | Portofolio |