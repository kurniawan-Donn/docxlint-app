docs/data_model.md
1. Finding
Field	Tipe	Deskripsi
finding_id	string	ID stabil dalam sesi.
rule_id	string	ID aturan, mis. SPELL_001.
category	enum	spelling, punctuation, repeated_word, foreign_italic, formatting.
severity	enum	info, low, medium, high.
location	object	Lokasi terstruktur.
original_value	string	Teks asli yang ditemukan.
suggested_value	string/null	Saran koreksi.
reason	string	Alasan temuan.
confidence	float 0–1	Keyakinan sistem.
review_status	enum	pending, accepted, rejected, conflict.
application_status	enum	not_applied, applied, failed, skipped, stale.
metadata	object	Info tambahan, mis. style, run properties.
2. Location
Field	Deskripsi
snapshot_id	ID snapshot dokumen saat analisis.
part	document, header, footer.
section_index	Indeks section jika relevan.
block_path	Path ke blok, mis. body/p[3]/table[0]/row[2]/cell[1]/p[0].
block_type	paragraph, table_cell, heading, list_item, hyperlink.
run_index	Indeks run dalam blok.
char_start	Offset awal dalam teks run.
char_end	Offset akhir dalam teks run.
global_text_offset	Opsional, offset dalam teks gabungan blok.
original_text_hash	Hash teks sekitar untuk cek stale.
3. Validitas Lokasi untuk Temuan Berdekatan
Semua offset mengacu pada snapshot awal dan tidak diubah selama review.

Jika beberapa temuan berada di run yang sama, simpan posisi asli masing-masing.

Saat menerapkan, urutkan berdasarkan posisi terbalik (dari belakang ke depan) agar offset tidak bergeser.

Jika temuan tumpang tindih, tandai conflict; jangan terapkan otomatis.

Sebelum edit, lakukan stale check: bandingkan teks saat ini dengan original_value dan hash.

Jika run dipecah atau diubah oleh edit lain, lokasi dianggap stale dan perlu review ulang.

4. Status
review_status: keputusan pengguna.

application_status: hasil penerapan.

Temuan rejected tidak pernah diterapkan.

Temuan accepted tetapi stale tidak diterapkan dan diberi tahu.

# Data Model (Phase 1.5 Update)

## Tambahan Field
- `application_status`: `not_applied`, `applied`, `failed`, `skipped`, `stale`, `conflict`.
- `original_text_hash` di `location`.
- `snapshot_id` di `location`.

## Aturan
- `conflict` tidak diterapkan.
- `stale` tidak diterapkan.
- `failed` memicu rollback opsional.