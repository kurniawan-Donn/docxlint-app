# UI Metrics — Dashboard Tinjauan

## Definisi
| Metric | Sumber | Aturan hitung |
|---|---|---|
| Total temuan | unique `finding_id` | Dedupe; jangan jumlahkan per kategori. |
| Kemungkinan salah eja | `category = spelling` | Setelah dedupe. |
| Kata tidak dikenal | `category = unknown_word` | Setelah dedupe. |
| Istilah asing | `category = foreign_term` | Setelah dedupe. |
| Isu italic | `category = italic_formatting` | Setelah dedupe. |
| Uncertain | `confidence < 0.85` | Setelah dedupe. |
| Dilewati | `application_status = skipped` | Setelah dedupe. |
| Conflict | `review_status = conflict` | Setelah dedupe. |
| Dipilih | `finding_id` di `selected_ids` | Berdasarkan SelectionState. |

## Anti double-counting
Total = jumlah unik `finding_id`. Kategori dihitung setelah dedupe.

## Metric yang dihilangkan
Jika sebuah metrik tidak didukung data (mis. tidak ada temuan
`foreign_term`), nilainya 0; tetap ditampilkan sebagai angka netral.

## Perubahan saat filter aktif
Metrik dashboard **selalu** menghitung seluruh findings yang tersedia,
bukan hanya visible. Untuk visible count, gunakan caption
"Menampilkan X dari Y temuan".