# Local Mode Enforcement

## 1. Tujuan
Menjamin mode lokal tidak pernah mengirim isi dokumen ke internet.

## 2. Network Guard
- Instal hook pada `socket.socket.connect` dan `socket.create_connection`.
- Blokir semua koneksi keluar kecuali `localhost`/`127.0.0.1`.
- Jika ada percobaan → raise `LocalModeNetworkBlocked` dan catat di log (tanpa isi dokumen).
- Hook aktif selama pemrosesan dokumen.

## 3. Disable Telemetry
- Set `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`.
- Set `STREAMLIT_SERVER_HEADLESS=true` saat perlu.
- Tidak mengaktifkan analytics.
- Tidak memakai layanan eksternal untuk logging.

## 4. Audit Dependensi
- Daftar dependensi diperiksa manual sebelum rilis.
- Library yang melakukan network call (mis. `requests`) tidak disertakan di mode lokal.
- Import diblokir kecuali untuk UI.

## 5. Test Socket/Outbound
- Unit test: aktifkan network guard, panggil `socket.create_connection(("example.com", 80))`, pastikan raise.
- Integration test: jalankan pipeline penuh, pastikan tidak ada exception network.
- Test audit: grep import untuk modul network di modul inti.

## 6. Kebijakan Update Kamus Offline
- Kamus lokal berupa file teks/CSV di repo atau folder `config/`.
- Update hanya via penggantian file manual.
- Tidak ada auto-download.
- Versi kamus dicatat di `config/dictionary_version.txt`.

## 7. Mode Demo Publik
- Bukan mode lokal.
- Boleh memakai resource server, tapi tetap tanpa layanan eksternal untuk konten.
- Cleanup file sementara wajib.
- Peringatan jelas ke pengguna.

## 8. DECISION
- DECISION-010: Network guard aktif di mode lokal. **Status: FINAL.**
- DECISION-011: Update kamus manual. **Status: FINAL.**
- DECISION-012: Demo publik bukan lingkungan privat. **Status: FINAL.**