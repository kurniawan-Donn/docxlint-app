# Rule Engine

## 1. Tujuan
Menjelaskan bagaimana DocxLint membedakan typo dari istilah teknis tak dikenal, serta bagaimana confidence, severity, dan status unknown ditentukan.

## 2. Kategori Aturan
- `spelling`: ejaan bahasa Indonesia.
- `punctuation`: tanda baca, spasi, tanda hubung.
- `repeated_word`: kata berulang.
- `foreign_italic`: istilah asing yang perlu italic.
- `formatting`: font, ukuran, margin, spasi, indentasi, alignment, heading, list.

## 3. Membedakan Typo vs Istilah Teknis
Alur keputusan:
1. Tokenisasi teks.
2. Normalisasi (lowercase, lepaskan tanda baca).
3. Cek whitelist/exception → jika ada, **bukan typo**.
4. Cek kamus lokal → jika ada, **bukan typo**.
5. Cek pola morfologi Indonesia (awalan/akhiran) → jika cocok, turunkan confidence.
6. Cek pola akronim/kapitalisasi (semua kapital, CamelCase) → tandai `unknown`, bukan typo.
7. Cek pola istilah teknis (mengandung angka, underscore, dot) → `unknown`.
8. Jika tidak ada yang cocok → `unknown` dengan confidence rendah, bukan langsung typo.
9. Hanya jika ada saran edit distance dekat dan aturan ejaan yakin → `spelling` dengan confidence tinggi.

## 4. Whitelist, Exception, Akronim, Kapitalisasi, Morfologi
- **Whitelist**: kata yang selalu dianggap benar (mis. `docx`, `streamlit`).
- **Exceptions**: pengecualian yang tidak boleh diubah walau di luar kamus.
- **Akronim**: `[A-Z]{2,}` atau campuran → `unknown`, tidak diubah.
- **Kapitalisasi**: cek proper noun; jangan ubah kapitalisasi nama merek.
- **Morfologi Indonesia**: awalan `me-`, `ber-`, `ter-`, `di-`, `ke-`; akhiran `-kan`, `-nya`, `-lah`, `-kah`. Jika kata dasar ada di kamus → bukan typo.

## 5. Confidence, Severity, Status Unknown
| Confidence | Label | Aksi |
|---|---|---|
| ≥ 0.85 | tinggi | Saran kuat, tetap perlu persetujuan. |
| 0.60–0.84 | sedang | Manual review. |
| 0.40–0.59 | rendah | Info, status `unknown`. |
| < 0.40 | sangat rendah | Tidak ditampilkan sebagai saran. |

Severity:
- `high`: kesalahan ejaan jelas, tanda baca yang mengubah makna.
- `medium`: ejaan, italic istilah asing.
- `low`: format ringan.
- `info`: unknown, saran.

## 6. Kapan Manual Review
- Confidence < 0.85.
- Status `unknown`.
- Overlap.
- Fitur tidak didukung.
- Perubahan format.

## 7. Contoh False Positive dan Cara Menghindari
| Contoh | Penyebab | Mitigasi |
|---|---|---|
| `docx` dianggap typo | Tidak ada di kamus | Whitelist. |
| `Streamlit` dianggap typo | Kapitalisasi | Whitelist + deteksi proper noun. |
| `me-render` dianggap typo | Tanda hubung | Normalisasi morfologi. |
| `API` dianggap typo | Akronim | Deteksi akronim. |
| `e-mail` dianggap typo | Ejaan baku | Exception list. |
| Kata Inggris dianggap perlu italic otomatis | Aturan kaku | Hanya italic jika ada di terminology list. |

## 8. Aturan Italic Istilah Asing
- Italic hanya diterapkan jika istilah ada di `terminology.csv` dengan flag `italic: true`.
- Tidak otomatis untuk semua kata Inggris.
- Confidence tinggi hanya jika istilah persis cocok.

## 9. DECISION
- DECISION-007: Unknown ≠ typo. **Status: FINAL.**
- DECISION-008: Threshold confidence final: 0.85 / 0.60 / 0.40. **Status: FINAL.**
- DECISION-009: Italic hanya dari terminology list. **Status: FINAL.**