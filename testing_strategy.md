1. Unit Test
Aturan ejaan, tanda baca, kata berulang, italic.

Pemetaan lokasi teks ke run.

Model finding.

Validasi konfigurasi.

Deteksi overlap dan stale.

2. Integration Test
Baca DOCX → analisis → terapkan → simpan → buka kembali.

Verifikasi teks berubah dan format run tetap.

Tabel, header, footer, hyperlink, list.

3. Regression Test
Fixture DOCX dengan temuan yang diketahui.

Bandingkan hasil dengan ekspektasi.

Pastikan aturan konservatif tidak menghasilkan false positive berlebihan.

4. Malformed File
ZIP rusak.

DOCX tanpa word/document.xml.

XML tidak valid.

Zip bomb.

Path traversal.

File terlalu besar.

5. Complex DOCX
Tabel bersarang.

Header/footer berbeda per section.

Hyperlink.

Multilevel list.

Style inheritance.

Run terpecah.

6. Formatting Preservation
Bandingkan rPr, pPr, style, dan struktur XML.

Pastikan teks di luar temuan tidak berubah.

Pastikan fitur tidak didukung ditandai, bukan dihapus.

7. Privacy
Mock network; pastikan tidak ada panggilan keluar di mode lokal.

Pastikan log tidak memuat konten dokumen.

Pastikan file sementara terhapus.

8. Acceptance Criteria Terukur
100% file malformed ditolak dengan pesan jelas.

0 panggilan jaringan pada mode lokal.

≥ 95% temuan benar pada korpus uji terkurasi.

Perubahan teks sederhana mempertahankan format run ≥ 95%.

Tidak ada crash pada fixture kompleks.

Semua temuan memiliki finding_id, rule_id, dan status.

File sementara demo terhapus setelah sesi.

Dokumen ≤ 10 MB diproses < 60 detik pada mesin uji standar.

# Testing Strategy (Phase 1.5 Update)

## Test Baru
- UT-18: network guard.
- UT-19: zip bomb.
- UT-20: malformed DOCX.
- IT-06: format preservation.
- IT-10: demo cleanup.
- IT-11: privacy no log content.
- IT-12: limits.
- IT-13: portability.

## Acceptance
- 0 outbound call di mode lokal.
- Semua `failed` terdeteksi.
- Rollback berfungsi.