# Format Preservation

## 1. Tujuan
Menjelaskan bagaimana DocxLint mengubah teks di dalam DOCX tanpa membangun ulang dokumen dari plain text, serta mempertahankan format run sejauh mungkin.

## 2. Prinsip
- Dokumen diperlakukan sebagai pohon OOXML (`document.xml`, `header*.xml`, `footer*.xml`, dll).
- Perubahan dilakukan pada level run, bukan pada level plain text global.
- Tidak ada rekonstruksi ulang seluruh body dari string.
- Jika perubahan tidak dapat dilakukan dengan aman, temuan ditandai `failed` atau `skipped`, bukan dipaksa.

## 3. Algoritma Mengubah Satu Kata di Dalam Run

### 3.1 Prasyarat
- Lokasi temuan: `part`, `block_path`, `run_index`, `char_start`, `char_end`.
- Snapshot awal dan `original_text_hash` tersedia.
- Temuan disetujui pengguna.

### 3.2 Langkah
1. **Resolve run**: ambil objek `python-docx` `Run` pada `block_path[run_index]`.
2. **Stale check**: bandingkan `run.text[char_start:char_end]` dengan `original_value` dan hash. Jika berbeda → `application_status = stale`.
3. **Kasus A – perubahan hanya di dalam satu run**:
   - Ambil `rPr` asli (`run._element.rPr`).
   - Buat elemen `<w:t>` baru dengan teks hasil (`new_text = run.text[:char_start] + suggested_value + run.text[char_end:]`).
   - Salin `xml:space="preserve"` bila teks memiliki spasi di ujung.
   - Ganti isi run: hapus `<w:t>` lama, sisipkan `<w:t>` baru, pertahankan `rPr`.
4. **Kasus B – perubahan mencakup batas run (mis. `char_end` melewati run)**:
   - Pecah run menjadi tiga bagian logis: prefix, target, suffix.
   - Buat run baru untuk tiap bagian dengan `rPr` disalin dari run asli.
   - Hapus run asli, sisipkan tiga run pada posisi yang sama.
   - Terapkan `suggested_value` pada bagian target.
5. **Kasus C – perubahan mengubah format (italic, bold)**:
   - Jika `suggested_value` memerlukan `rPr` berbeda (mis. italic untuk istilah asing), buat run baru dengan `rPr` yang dimodifikasi.
   - Jangan mengubah `rPr` run tetangga.
6. **Update `application_status`**: `applied` jika sukses, `failed` jika exception.

### 3.3 Contoh XML Sebelum
```xml
<w:p>
  <w:r>
    <w:rPr><w:b/></w:rPr>
    <w:t>kata salah ejaan disini</w:t>
  </w:r>
</w:p>