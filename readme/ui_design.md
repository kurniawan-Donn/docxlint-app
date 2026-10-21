# UI Design — Phase 7.5

Dokumen ini menjelaskan design system tampilan Streamlit DocxLint:
token, komponen, aksesibilitas, dan limitasi. Sumber kebenaran token ada di
`src/docxlint/ui/theme.py`; `.streamlit/config.toml` menyalin nilai dasar
untuk tema bawaan Streamlit.

## 1. Arsitektur tampilan

```text
app.py                 inject_theme → sidebar → upload → validasi/baca → tab stage
ui/theme.py            token + build_css() + inject_theme()
ui/components.py       helper murni (dapat ditest) + render_* (Streamlit)
ui/review_view.py      helper murni Tinjauan: lingkup, grup, urutan, paginasi
ui/sections/summary.py   Ringkasan
ui/sections/checks.py    Pemeriksaan
ui/sections/review.py    Tinjauan  (logika Phase 5 dipindah apa adanya)
ui/sections/repair.py    Perbaikan (logika Phase 6/7 dipindah apa adanya)
ui/sections/export.py    Ekspor
```

- Status bar, badge row, dan status sidebar **diisi paling akhir** dalam
  satu rerun (lewat container placeholder) agar mencerminkan hasil tombol
  yang baru ditekan.
- Semua pemrosesan dokumen tetap di dalam `network_guard()`.
- Key `session_state` yang sudah ada tidak diubah. Key baru:
  `_snapshot_cache` (snapshot per hash file), `repair_critical`,
  `chk_review_unlisted`, `btn_check_*`, `dl_roundtrip`,
  `dl_repaired_export`, `rv_scope`, `rv_view`, `rv_page`, `grp_*`,
  `rsg_*`.
- **Ganti file**: bila hash file berubah, *isi* key per dokumen
  (`findings`, `foreign_findings`, `fmt_findings`, `repair_*`, filter,
  halaman) direset dan `SelectionState` di-reset ke snapshot baru. Nama
  key tidak berubah. Ini mencegah temuan file lama tampil atau diterapkan
  ke file baru.

## 1a. Chrome halaman

- **Header (hero)**: logo SVG inline, judul "DocxLint" bergradien
  accent→violet, tagline, badge mode. Mode demo publik aktif bila env
  `DOCXLINT_PUBLIC_DEMO` bernilai `1/true/ya/on` (di Streamlit Cloud: isi
  lewat Secrets) dan menambah banner peringatan.
- **Status bar + stepper**: diisi paling akhir dalam rerun. Stepper memakai
  `stepper_steps()` (murni) dan menandai tahap aktif dengan
  `aria-current="step"`.
- **Landing**: dropzone uploader bergaris putus accent + empat kartu fitur
  dengan ikon SVG inline (tanpa CDN ikon).
- **Sidebar**: brand, status dokumen, status pemeriksaan (badge), profil.
- **Footer**: versi paket + pernyataan pemrosesan lokal.

## 2. Design tokens

### Warna

| Token | Hex | Pemakaian |
|-------|-----|-----------|
| `bg` | `#FAFAFA` | Latar aplikasi |
| `surface` | `#FFFFFF` | Card, tabel, status bar |
| `border` | `#E5E7EB` | Border card dan tabel |
| `text` | `#111827` | Teks utama |
| `secondary` | `#6B7280` | Teks sekunder di atas putih/bg |
| `muted_text` | `#4B5563` | Teks pill netral di atas `neutral_soft` |
| `accent` | `#2563EB` | Aksi utama, card terpilih |
| `success` / `success_text` | `#059669` / `#047857` | Border / teks sukses |
| `warning` / `warning_text` | `#D97706` / `#B45309` | Border / teks peringatan |
| `danger` / `danger_text` | `#DC2626` / `#B91C1C` | Border / teks error |
| `*_soft` | — | Latar pill dan banner |

`success` dan `warning` dasar **tidak** lolos 4.5:1 untuk teks di atas putih
(≈3.8:1 dan ≈3.2:1). Karena itu dipakai hanya untuk border/aksen; teks
memakai varian `*_text`. `secondary` di atas `neutral_soft` hanya ≈4.39:1,
sehingga pill netral memakai `muted_text`.

### Mode gelap

`DARK` memiliki token yang sama persis dengan `LIGHT` (diuji). CSS
mendeklarasikan variabel `--dl-*` pada `.stApp` dengan
`light-dark(terang, gelap)`. Streamlit memasang `color-scheme: light|dark`
pada `.stApp` sesuai tema aktif, sehingga warna kustom ikut berganti seketika
saat pengguna mengganti tema, tanpa rerun. `st.context.theme` sengaja tidak
dipakai karena dapat keliru saat halaman pertama dimuat (Streamlit #11920).
Browser tanpa `light-dark()` (sebelum 2024) memakai palet terang.

Semua pasangan `TEXT_PAIRS` diuji ≥ 4.5:1 untuk **kedua** palet.

### Spasi, radius, tipografi

- Spasi: 4 / 8 / 12 / 16 / 24 / 32 px.
- Radius: 6 px (kecil), 10 px (banner, tabel, kontrol), 12 px (card, metrik), 16 px (hero, dropzone); pill 999 px.
- Shadow: halus, hanya untuk logo, tab aktif, dan hover card (token `shadow`).
- Font: `system-ui` stack; mono untuk lokasi (`ui-monospace`, Consolas).
- Ukuran: dasar 14 px, heading 20–26 px, judul hero 26 px.

## 3. Komponen

| Fungsi | Jenis | Keterangan |
|--------|-------|------------|
| `severity_color`, `severity_tone`, `severity_label` | murni | Severity → warna teks/tone/label Indonesia |
| `confidence_label` | murni | `Yakin · 0,92` (band DECISION-008) |
| `badge_text_for_state` | murni | Teks badge: belum/sudah diperiksa, N dipilih, perbaikan siap/diblokir |
| `check_badges`, `repair_state`, `stage_progress`, `file_status` | murni | Turunan dari `session_state` |
| `format_location`, `format_file_size`, `document_stats`, `status_bar_text` | murni | Format teks |
| `finding_header_html`, `change_plan_table_html`, `pill_html` | murni | HTML ter-escape |
| `render_status_bar`, `render_badges`, `render_metric_row` | render | — |
| `render_finding_card` | render | Pill kategori + severity + confidence, nilai asli → saran, alasan, lokasi mono |
| `render_empty_state`, `render_error_banner`, `render_warning_banner`, `render_success_banner`, `render_meta_card` | render | — |

### Card temuan (Tinjauan)

1. Baris pill: kategori · severity · confidence.
2. `original_value` tebal → saran (hijau).
3. Alasan (abu-abu).
4. Lokasi mono: `body/p[3] run[0] 12–18`.
5. Baris aksi: checkbox **Pilih**, radio status tinjauan, expander **Detail**.

Card terpilih mendapat border kiri accent 4 px dan latar `accent_soft`
melalui CSS `:has(input:checked)`, tanpa mengganti key container.

### Mengurangi kebisingan di Tinjauan

Kamus lokal masih kecil, sehingga sebagian besar temuan berupa "kata tidak
dikenal". Tinjauan karena itu memakai empat lapis penyaring:

1. **Lingkup** (default *Perlu tindakan*). *Perlu tindakan* = temuan yang
   didukung perbaikan otomatis (ejaan dengan saran, atau italic dengan
   `expected_italic=true`), sama persis dengan aturan tab Perbaikan.
   *Informasi* = sisanya. *Semua* = keduanya.
2. **Tampilan** (default *Per kata*). Temuan dengan kategori, kata
   (tanpa beda huruf besar/kecil), dan saran yang sama digabung menjadi satu
   card dengan pill "N lokasi". Checkbox *Pilih semua (N)* dan radio status
   berlaku untuk semua anggota; daftar lokasi ada di expander. Bila hanya
   sebagian anggota dipilih, card menampilkan "X dari N lokasi dipilih".
   `selected_ids` tetap satu-satunya sumber kebenaran pilihan.
3. **Urutan prioritas**: dapat diperbaiki → severity → confidence →
   lokasi dokumen. Kelompok besar didahulukan bila prioritasnya sama.
4. **Paginasi**: 20 card per halaman dengan tombol *Sebelumnya* /
   *Berikutnya*. Halaman kembali ke 1 setiap kali lingkup, tampilan, atau
   filter berubah. Tombol pilih massal tetap berlaku untuk semua halaman.

Metrik utama diringkas menjadi Total / Perlu tindakan / Informasi /
Dipilih; rincian per kategori ada di expander.

### Filter bar

Tiga baris sticky: (1) lingkup, tampilan, pilihan; (2) pencarian dan
popover *Filter lanjutan* (status tinjauan/aplikasi); (3) chip
kategori/severity/confidence (`st.pills`). Opsi chip mengikuti lingkup
aktif, dan nilai yang tidak lagi tersedia dibuang otomatis. Hitungan "Menampilkan X dari Y temuan" selalu
tampil, dan ada empty state bila filter tidak menyisakan apa pun.

### Perbaikan

Tabel change plan (Status | Operasi | Original → Pengganti | Lokasi |
Alasan), card konfirmasi dengan satu checkbox wajib, tombol
**Terapkan Perubahan** nonaktif sampai dicentang, metrik hasil, daftar gagal
yang bisa dilipat. Unduhan hanya muncul jika validasi output lolos dan tidak
ada kegagalan kritis.

## 4. Aksesibilitas

- Status tidak hanya bergantung pada warna: setiap pill memakai warna, ikon
  simbol (▲ ◆ ● ○ ✓ ✕ !), dan teks.
- Kontras teks ≥ 4.5:1 diuji otomatis untuk setiap pasangan di
  `TEXT_PAIRS` (`tests/test_ui_helpers.py`).
- Semua widget memiliki label Indonesia. Label yang disembunyikan secara
  visual (radio status) tetap ada untuk pembaca layar; tombol massal
  memiliki `help=`.
- Emoji hanya dipakai sebagai indikator stage (tab, checklist) dan ikon
  file di status bar. Ikon dekoratif diberi `aria-hidden`.
- Banner error memakai `role="alert"`; status bar memakai `role="status"`.

## 5. Keamanan tampilan

Teks dari dokumen (nilai asli, saran, alasan, nama file) di-escape dengan
`html.escape` sebelum masuk HTML `unsafe_allow_html`. Banner error tidak
menampilkan traceback maupun isi dokumen.

## 6. Limitasi

- **Sticky filter bar** bergantung pada kelas `.st-key-*` dan struktur
  `stLayoutWrapper` Streamlit 1.65. Bila struktur DOM berubah saat upgrade,
  bar tetap berfungsi tetapi tidak lagi sticky.
- **Tab tidak dapat dipindah dari kode**; checklist di sidebar hanya
  indikator progres.
- `toolbarMode = "minimal"` menyembunyikan tombol Deploy/Rerun dari
  pengunjung; saat mengembangkan, restart server setelah mengubah modul.
- Gaya tab bergantung pada `[data-testid=stTab]` (Streamlit 1.65).
- Semua tab dirender setiap rerun (perilaku `st.tabs`), termasuk pembuatan
  change plan di tab Perbaikan.
- Hitungan paragraf mengikuti metrik lama: paragraf di dalam sel tabel ikut
  dihitung.
- Temuan format tampil di tab Pemeriksaan saja; belum masuk alur Tinjauan
  dan Perbaikan.
- Filter bar sticky setinggi sekitar 210 px pada layar 900 px.
- Sumber utama kebisingan adalah data, bukan UI: kamus kecil membuat kata
  umum ditandai "tidak dikenal", dan kata dalam istilah glossary
  (mis. *machine*, *learning*) juga ditandai terpisah oleh pemeriksa bahasa.
