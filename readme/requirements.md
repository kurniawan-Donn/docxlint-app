docs/requirements.md
1. Tujuan
DocxLint adalah aplikasi Python + Streamlit untuk memeriksa dan secara selektif memperbaiki dokumen DOCX berbahasa Indonesia yang mengandung istilah Inggris, pola ejaan, tanda baca, kata berulang, aturan italic istilah asing, dan format dokumen yang dapat dikonfigurasi.

2. Ruang Lingkup MVP
Satu DOCX per sesi pemrosesan.

Pemeriksaan lokal tanpa internet.

Tidak menggunakan AI generatif.

Menampilkan temuan sebelum perubahan diterapkan.

Perbaikan hanya diterapkan pada temuan yang disetujui pengguna.

Mendukung paragraf, run, tabel, header, footer, hyperlink, dan multilevel list sejauh didukung python-docx dan struktur OOXML.

Aturan bahasa dan format dapat dikonfigurasi.

Mode lokal tidak mengirim konten dokumen ke layanan eksternal.

Demo publik hanya untuk dokumen non-sensitif.

3. Fakta, Asumsi, dan Rekomendasi
Fakta yang perlu diverifikasi sebelum implementasi:

Versi stabil python-docx, streamlit, lxml, dan dependensi lain.

Lisensi sumber kamus/istilah yang akan dipakai.

Batas resource Streamlit Community Cloud.

Perilaku python-docx terhadap fitur DOCX kompleks.

Asumsi:

Pengguna utama adalah satu pengguna lokal atau demo publik non-sensitif.

Dokumen DOCX umumnya berukuran kecil hingga sedang.

Sebagian besar dokumen tidak memakai fitur Word lanjutan seperti tracked changes, content control, atau equation.

Rekomendasi:

Mulai dari aturan konservatif: lebih baik menandai “perlu ditinjau” daripada otomatis mengubah.

Jangan menganggap setiap kata yang tidak ada di kamus sebagai typo.

Jangan otomatis meng-italic-kan semua kata Inggris.

Jangan menjanjikan preservasi sempurna semua fitur Word.

4. Functional Requirements
ID	Requirement	Prioritas
FR-01	Pengguna dapat mengunggah satu file DOCX.	Wajib
FR-02	Sistem memvalidasi file DOCX/ZIP sebelum diproses.	Wajib
FR-03	Sistem mengekstrak teks dari paragraf, run, tabel, header, footer, hyperlink, dan list.	Wajib
FR-04	Sistem menjalankan aturan ejaan, tanda baca, kata berulang, istilah asing, dan format.	Wajib
FR-05	Sistem menampilkan temuan dengan lokasi, nilai asli, saran, alasan, severity, dan confidence.	Wajib
FR-06	Pengguna dapat menerima, menolak, atau menandai temuan untuk ditinjau.	Wajib
FR-07	Sistem hanya menerapkan temuan yang disetujui.	Wajib
FR-08	Sistem mempertahankan format run dan struktur dokumen sejauh mungkin.	Wajib
FR-09	Sistem mendeteksi lokasi basi/stale sebelum menerapkan perubahan.	Wajib
FR-10	Sistem menangani temuan yang tumpang tindih.	Wajib
FR-11	Sistem menyimpan hasil koreksi ke DOCX baru.	Wajib
FR-12	Sistem menampilkan peringatan untuk fitur yang tidak didukung.	Wajib
FR-13	Aturan dapat dikonfigurasi melalui file konfigurasi.	Wajib
FR-14	Kamus lokal, daftar istilah, pengecualian, dan aturan italic dapat dikonfigurasi.	Wajib
FR-15	Sistem dapat menghasilkan ringkasan temuan.	Sebaiknya
FR-16	Sistem mendukung pemeriksaan format font, ukuran, margin, spasi, indentasi, alignment, heading, dan list.	Wajib
FR-17	Sistem dapat melakukan perbaikan format yang aman jika disetujui.	Sebaiknya
FR-18	Mode lokal tidak melakukan panggilan jaringan eksternal.	Wajib
FR-19	Demo publik membatasi ukuran file dan menghapus file sementara.	Wajib
FR-20	Sistem tidak menyimpan konten dokumen secara permanen.	Wajib
5. Non-Functional Requirements
ID	Requirement	Target
NFR-01	Local-first	Semua pemeriksaan inti berjalan tanpa internet.
NFR-02	Privasi	Tidak ada konten dokumen di log, cache, atau layanan eksternal pada mode lokal.
NFR-03	Keamanan	Validasi ZIP, batas ukuran, batas waktu, dan penolakan file mencurigakan.
NFR-04	Kinerja	Dokumen ≤ 10 MB diproses < 60 detik pada mesin standar.
NFR-05	Reliabilitas	Tidak crash pada file malformed; beri error yang jelas.
NFR-06	Preservasi format	Perubahan teks sederhana mempertahankan format run.
NFR-07	Auditabilitas	Setiap temuan punya finding_id, rule_id, dan status.
NFR-08	Portabilitas	Berjalan di Windows/Linux/macOS dengan Python yang didukung.
NFR-09	Maintainability	Modul terpisah: baca, tulis, aturan, konfigurasi, UI.
NFR-10	Skalabilitas demo	Demo publik membatasi resource dan tidak untuk dokumen sensitif.
6. Batasan MVP
Tidak ada AI generatif.

Tidak ada database.

Tidak ada autentikasi.

Tidak ada microservices.

Tidak ada jaminan preservasi semua fitur Word.

Tidak ada akses resmi gratis ke KBBI yang diasumsikan.

Tidak ada pemrosesan multi-dokumen dalam satu sesi.

Tidak ada koreksi otomatis tanpa persetujuan.

# Requirements (Phase 1.5 Update)

## Perubahan
- Angka final: max 10 MB, timeout 60 s, max 2000 entri ZIP, rasio kompresi 100:1, max uncompressed 100 MB, max findings 5000.
- Threshold confidence: 0.85 / 0.60 / 0.40.
- Unknown ≠ typo.
- Italic hanya dari terminology list.
- Rollback in-memory wajib.
- Network guard wajib di mode lokal.

## FR Tambahan
- FR-21: Preview diff sebelum apply.
- FR-22: Rollback jika validasi gagal.
- FR-23: Blokir unduh jika ada `failed` kritis.

## NFR Tambahan
- NFR-11: Network guard lokal.
- NFR-12: Audit dependensi.