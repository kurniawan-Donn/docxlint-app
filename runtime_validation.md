# Runtime Validation

## 1. Tujuan
Memastikan setiap perbaikan divalidasi sebelum DOCX diunduh.

## 2. Preview Diff Sebelum Apply
- Setelah analisis, tampilkan tabel: `finding_id`, lokasi, `original_value`, `suggested_value`, `reason`, `confidence`.
- Tampilkan diff teks per blok yang akan berubah.
- Pengguna memilih accept/reject per finding.

## 3. Validasi Per Finding Setelah Apply
- Setelah apply, ambil teks di lokasi.
- Bandingkan dengan `suggested_value`.
- Bandingkan format run (`rPr`) sebelum dan sesudah.
- Jika cocok → `application_status = applied`.
- Jika teks tidak cocok → `failed`.
- Jika lokasi bergeser → `stale`.

## 4. Status
| Status | Arti |
|---|---|
| `applied` | Berhasil dan tervalidasi. |
| `failed` | Gagal diterapkan. |
| `stale` | Lokasi berubah. |
| `skipped` | Fitur tidak didukung atau ditolak. |
| `conflict` | Overlap dengan finding lain. |

## 5. Rollback
- Simpan salinan in-memory `Document` sebelum apply.
- Jika ada finding `failed` kritis (mis. > 0 dan menyentuh body utama), tawarkan rollback.
- Jika rollback dipilih, kembalikan ke `Document` awal.
- Batalkan tombol unduh sampai validasi lolos.

## 6. Validasi Global Sebelum Unduh
- Semua finding disetujui harus `applied` atau `skipped` dengan alasan.
- Tidak boleh ada `failed` tanpa pemberitahuan.
- Jika ada `failed`, tampilkan peringatan dan opsi:
  - Unduh tanpa perubahan gagal.
  - Rollback dan ulangi.

## 7. DECISION
- DECISION-013: Rollback in-memory. **Status: FINAL.**
- DECISION-014: Unduh diblokir jika ada `failed` kritis. **Status: FINAL.**