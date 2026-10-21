# Dictionary — DocxLint

## DECISION-018 (FINAL)
Sumber kamus default: **wordlist Bahasa Indonesia yang dikurasi manual**
di `config/dictionary_id.txt`, disusun oleh maintainer DocxLint untuk
keperluan portofolio dan penggunaan lokal.

- **Versi**: mengikuti isi repo (lihat commit terakhir file).
- **Lisensi**: CC0 / public domain untuk isi wordlist repo ini.
- **Atribusi**: disusun manual; tidak mengambil dari KBBI.
- **Redistribusi**: bebas (CC0).
- **Instruksi pemasangan**: file sudah disertakan; tidak ada langkah
  tambahan.
- **Batasan**: wordlist ini **kecil dan tidak lengkap**. Bukan kamus
  komprehensif Bahasa Indonesia.

## Redistribusi KBBI
KBBI **tidak** boleh diasumsikan bebas untuk diredistribusi. DocxLint
tidak menyertakan, menyalin, atau mengambil data KBBI.

## API KBBI
Tidak ada asumsi API KBBI resmi gratis. DocxLint tidak melakukan
network call untuk kamus.

## Mengganti dengan Wordlist Sendiri
Pengguna dapat mengganti `config/dictionary_id.txt` dengan wordlist
berlisensi permisif yang sudah mereka verifikasi. Format:

- Satu kata per baris.
- UTF-8 tanpa BOM.
- Baris dimulai `#` diabaikan.
- Case-insensitive saat lookup.

Adapter di `DictionaryService` hanya membaca file lokal; tidak ada
download otomatis.

## Format File Lain
- `config/whitelist.txt`: token yang selalu dianggap benar.
- `config/exceptions.csv`: kolom `word, reason`.
- `config/terminology.csv`: kolom `term, italic, category, note`.

## Status Jika Kamus Hilang
Jika file utama hilang atau kosong, aplikasi tetap berjalan dan
menampilkan pesan "Kamus belum siap". Pemeriksaan bahasa tidak dijalankan
(menghindari false positive masif).