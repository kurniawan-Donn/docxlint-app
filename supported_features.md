# Supported Features

## 1. Klasifikasi
- **Penuh**: dibaca dan diubah dengan aman.
- **Peringatan**: dibaca, diubah terbatas, atau hanya diperingatkan.
- **Ditolak**: tidak diproses.

## 2. Daftar Fitur
| Fitur | Status | Alasan | Dampak |
|---|---|---|---|
| Paragraf | Penuh | API `python-docx` stabil. | Aman. |
| Run | Penuh | API stabil. | Aman. |
| Tabel | Penuh | API stabil, termasuk bersarang. | Aman. |
| Header/Footer | Penuh | API stabil. | Aman. |
| Hyperlink | Peringatan | API terbatas; butuh akses XML. | Edit bisa `skipped`. |
| Multilevel list | Peringatan | `numPr` dibaca, edit teks aman; ubah level = format. | Format list hanya diperingatkan. |
| Style bernama | Penuh | Dipertahankan. | Aman. |
| Font/ukuran | Peringatan | Cek & perbaikan aman terbatas. | Perbaikan opsional. |
| Margin | Peringatan | Cek via `sectPr`. | Perbaikan terbatas. |
| Line spacing | Peringatan | Cek via `pPr`. | Perbaikan terbatas. |
| Paragraph spacing | Peringatan | Cek via `pPr`. | Perbaikan terbatas. |
| Indentation | Peringatan | Cek via `pPr`. | Perbaikan terbatas. |
| Alignment | Peringatan | Cek via `pPr`. | Perbaikan terbatas. |
| Headings | Peringatan | Berdasarkan `pStyle`. | Perbaikan terbatas. |
| Comments | Ditolak | Tidak didukung `python-docx`. | Ditandai. |
| Tracked changes | Ditolak | Tidak didukung. | Ditandai. |
| Equations | Ditolak | Tidak didukung. | Ditandai. |
| Text boxes | Ditolak | Tidak didukung. | Ditandai. |
| SmartArt | Ditolak | Tidak didukung. | Ditandai. |
| Content controls | Ditolak | Tidak didukung stabil. | Ditandai. |
| Macros (.docm) | Ditolak | Keamanan. | File ditolak. |
| Embedded objects | Ditolak | Tidak diproses. | Ditandai. |
| Footnotes/Endnotes | Peringatan | Terbatas. | Ditandai. |

## 3. DECISION
- DECISION-015: Daftar di atas adalah baseline MVP. **Status: FINAL.**