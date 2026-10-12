docs/security_privacy.md
1. Mode Lokal
Tidak ada panggilan jaringan eksternal.

Tidak ada telemetry.

Tidak ada unggahan ke cloud.

File sementara dibuat lokal dan dihapus setelah sesi.

Log hanya metadata/error, bukan isi dokumen.

2. Demo Publik
Streamlit Community Cloud bukan lingkungan privat.

Hanya untuk dokumen non-sensitif.

File diproses di server demo.

Batas ukuran file, mis. 10 MB.

Batas waktu proses, mis. 60 detik.

Tidak ada penyimpanan permanen.

File sementara dihapus pada finally/sesi berakhir.

Tidak ada cache konten dokumen.

3. Validasi DOCX/ZIP
Tolak file bukan ZIP/DOCX.

Tolak .docm atau file dengan makro.

Batasi jumlah entri ZIP.

Batasi rasio kompresi untuk mencegah zip bomb.

Tolak path traversal.

Validasi XML well-formed.

Gunakan parser aman; defusedxml direkomendasikan.

Batasi ukuran tidak terkompresi.

4. Resource Exhaustion
Maksimum ukuran file.

Maksimum jumlah paragraf/tabel.

Maksimum jumlah temuan.

Timeout proses.

Error yang jelas jika batas terlampaui.

5. Cleanup
Hapus file upload sementara.

Hapus file hasil sementara setelah diunduh.

Bersihkan session state Streamlit.

Jangan menulis konten ke disk kecuali perlu dan sementara.

# Security & Privacy (Phase 1.5 Update)

## Angka Final
- Max file: 10 MB.
- Max uncompressed: 100 MB.
- Max ZIP entries: 2000.
- Max compression ratio: 100:1.
- Timeout: 60 s.
- Max findings: 5000.

## Network Guard
- Aktif di mode lokal.
- Hook pada socket.
- Test wajib.

## Cleanup
- Hapus file sementara di `finally`.
- Tidak menyimpan konten di log.