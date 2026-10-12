1. Gaya Arsitektur
Arsitektur modular monolitik sederhana. Satu aplikasi Streamlit, satu proses lokal, tanpa backend terpisah.

2. Modul dan Tanggung Jawab
Modul	Tanggung Jawab	Batas
ui	Streamlit: upload, konfigurasi, review temuan, tombol terapkan, unduh hasil.	Tidak berisi logika aturan atau manipulasi XML.
orchestrator	Mengatur alur: validasi → baca → analisis → review → tulis → validasi.	Tidak tahu detail XML.
docx_reader	Membaca DOCX, membangun indeks lokasi, mengekstrak teks dan run.	Tidak mengubah dokumen.
docx_writer	Menerapkan temuan yang disetujui, menjaga format, menyimpan DOCX.	Hanya menerima finding tervalidasi.
rule_engine	Menjalankan aturan dan menghasilkan finding.	Tidak menulis DOCX.
rules_*	Aturan spesifik: ejaan, tanda baca, kata berulang, italic, format.	Terpisah dan dapat dikonfigurasi.
dictionary	Kamus lokal, daftar istilah, pengecualian.	Tidak mengunduh data eksternal.
config	Skema konfigurasi dan validasi.	Tidak berisi aturan bisnis.
models	Data model finding, location, status.	Stabil dan tidak bergantung UI.
security	Validasi file, batas resource, cleanup.	Tidak membaca isi teks untuk aturan.
reporting	Ringkasan temuan dan ekspor.	Tidak mengubah dokumen.
3. Alur Utama
Pengguna mengunggah DOCX.

security memvalidasi ZIP, ukuran, entri, dan XML dasar.

docx_reader membangun snapshot dan indeks lokasi.

rule_engine menjalankan aturan dan menghasilkan finding.

ui menampilkan review.

Pengguna menerima/menolak.

docx_writer menerapkan perubahan yang disetujui.

docx_writer menyimpan dan memvalidasi hasil.

ui menyediakan unduhan.

4. Prinsip Desain
Jangan mengekstrak seluruh dokumen menjadi plain text lalu membangun ulang.

Jangan mengubah dokumen sebelum pengguna menyetujui.

Jangan menganggap fitur yang tidak didukung sebagai hilang; tandai.

Jangan membuat dependensi baru tanpa alasan MVP.

5. Struktur Proyek yang Diusulkan
text
docxlint/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── data_model.md
│   ├── security_privacy.md
│   ├── testing_strategy.md
│   ├── risks_and_tradeoffs.md
│   └── implementation_roadmap.md
├── config/
│   ├── default_rules.yaml
│   ├── dictionary_id.txt
│   ├── terminology.csv
│   └── exceptions.csv
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── fixtures/
└── (kode aplikasi dibuat pada Phase 2+)
6. Dependensi yang Diusulkan
Dependensi	Fungsi	Lisensi	Status
streamlit	UI web lokal/demo	Apache 2.0	Wajib
python-docx	Baca/tulis DOCX	MIT	Wajib
lxml	XML/OOXML	BSD	Wajib tidak langsung
defusedxml	Validasi XML aman	PSF-like	Opsional, direkomendasikan
pytest	Testing	MIT	Wajib untuk dev
pytest-cov	Coverage	MIT	Opsional
ruff	Lint	MIT	Opsional
mypy	Type check	MIT	Opsional
Catatan: versi dan lisensi harus diverifikasi sebelum implementasi. Jangan mengasumsikan versi saat ini.

# Architecture (Phase 1.5 Update)

## Modul Tambahan
| Modul | Tanggung Jawab |
|---|---|
| `network_guard` | Blokir outbound di mode lokal. |
| `validator` | Validasi per finding setelah apply. |
| `rollback` | Simpan snapshot in-memory dan pulihkan. |
| `diff_preview` | Hasilkan preview diff. |

## Alur Diperbarui
1. Upload → validate → read → analyze → review → apply → validate → preview → download.
2. Rollback tersedia jika validasi gagal.