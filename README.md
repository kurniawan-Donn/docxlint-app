# DocxLint — Phase 2

Alat pemeriksaan DOCX **local-first**. Phase 2 menyediakan fondasi:
unggah, validasi, baca struktur, dan ekspor round-trip.

## Lingkup Phase 2
**Sudah ada**
- UI Streamlit dasar (Bahasa Indonesia).
- Validasi file DOCX (ukuran, ZIP, komponen, makro, path traversal).
- Pembacaan paragraf, tabel, header/footer, style, deteksi run kompleks.
- Ekspor round-trip (byte identik).
- Network guard di mode lokal.
- Test `pytest` untuk layanan inti.

**Belum ada**
- Deteksi typo, ejaan, tanda baca, kata berulang.
- Deteksi istilah Inggris dan italic otomatis.
- Perbaikan format (font, ukuran, margin, spasi, indentasi, alignment).
- Edit selektif pada DOCX (writer masih no-op).
- Rollback berbasis bytes (akan datang di Phase 4).

## Persyaratan
- Python 3.10+
- Windows, Linux, atau macOS

## Instalasi

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Phase 3 — Local Language Checker

**Fitur baru**
- Deteksi kemungkinan salah eja Bahasa Indonesia (rule-based).
- Klasifikasi "kata tidak dikenal" terpisah dari typo.
- Saran koreksi deterministik (Levenshtein, maks 3).
- Kamus lokal + whitelist + exceptions + terminology.
- Tidak ada AI generatif, tidak ada API eksternal.
- **Tidak mengubah dokumen.** Hanya menampilkan temuan.

**Cara kerja kamus**
- Wordlist default di `config/dictionary_id.txt` (kurasi manual, CC0).
- Pengguna dapat mengganti dengan wordlist berlisensi permisif sendiri.
- Lihat `docs/dictionary.md`.

**Menambah istilah & pengecualian**
- `config/whitelist.txt`: token yang selalu dianggap benar.
- `config/exceptions.csv`: kolom `word, reason`.
- `config/terminology.csv`: kolom `term, italic, category, note`.

**Menjalankan**
```bash
streamlit run app.py
```

## Phase 4 — Istilah Asing dan Italic

**Fitur baru**
- Deteksi istilah asing terdaftar di `config/terminology.csv`.
- Deteksi frasa multi-kata (whitespace fleksibel).
- Inspeksi status italic: fully, partially, not, unknown.
- Rekomendasi italic **hanya** untuk term terdaftar (DECISION-009).
- Kandidat asing tak terdaftar bersifat **opt-in** dan ditandai uncertain.
- **Tidak ada auto-italic.** Tidak ada modifikasi DOCX.

**Konfigurasi**
- `config/terminology.csv`: kolom `term, italic, category, note` (wajib); `language, case_sensitive, priority` (opsional).
- `config/exceptions.csv`: suppress term.
- `config/whitelist.txt`: suppress token dari pemeriksaan bahasa.

**Batasan**
- Style inheritance yang tidak dapat diresolusi -> `unknown`.
- Hyperlink: run di dalam hyperlink belum diinspeksi (Phase 5).
- Run kompleks -> `skipped`.

**Kebijakan default**
- `review_configured_foreign_terms = True`
- `review_unlisted_foreign_candidates = False`
- `respect_existing_italic = True`

## Phase 7.5 — Modernisasi UI

Tampilan `app.py` disusun ulang tanpa mengubah backend (services, models,
repair engine). Alur tetap: upload → validasi → baca → analisis →
pratinjau → tinjauan → perbaikan → unduh.

**Layout**
- **Sidebar**: status file (diunggah / tervalidasi / dianalisis),
  checklist tahapan, pemilih profil formatting + badge versi.
- **Status bar** di atas: `📄 nama.docx • 36 KB • 9 paragraf • 1 tabel`.
- **Badge row**: status tiap pemeriksaan, jumlah temuan dipilih, status
  perbaikan.
- **Tab stage** di area utama:

| Tab | Isi |
|-----|-----|
| 📋 Ringkasan | Metadata dokumen, konfigurasi aktif, pratinjau struktur. |
| 🔍 Pemeriksaan | Tombol cek bahasa, istilah asing, dan format beserta metriknya. |
| 📝 Tinjauan | Filter bar sticky (cari + chip kategori/severity/confidence), toolbar pilih massal, card temuan. |
| 🛠️ Perbaikan | Tabel change plan, konfirmasi wajib, ringkasan hasil, unduhan. |
| 📦 Ekspor | Unduh round-trip dan hasil perbaikan (jika validasi lolos). |

Navigasi stage dilakukan lewat tab; checklist di sidebar hanya
menunjukkan progres (Streamlit tidak bisa berpindah tab dari kode).

**Struktur kode UI**
```text
app.py                         # orchestrator tipis
src/docxlint/ui/theme.py       # design tokens + inject_theme()
src/docxlint/ui/components.py  # helper murni + render_*
src/docxlint/ui/sections/      # satu modul per stage
.streamlit/config.toml         # tema dasar + gatherUsageStats=false
```

Folder section sengaja tidak bernama `pages/` agar Streamlit tidak
menganggapnya aplikasi multi-halaman. Detail design system ada di
`readme/ui_design.md`.
