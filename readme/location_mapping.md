
---

# docs/location_mapping.md

```markdown
# Location Mapping

## 1. Tujuan
Menjelaskan bagaimana `finding.location` dipetakan ke objek `python-docx` dan OOXML, serta bagaimana lokasi tetap valid saat beberapa temuan berdekatan.

## 2. Struktur Location

location = {
snapshot_id, part, section_index, block_path,
block_type, run_index, char_start, char_end,
global_text_offset, original_text_hash
}


## 3. Pemetaan block_path ke Objek
| block_path contoh | Objek |
|---|---|
| `body/p[3]` | `document.paragraphs[3]` |
| `body/table[0]/row[2]/cell[1]/p[0]` | `document.tables[0].rows[2].cells[1].paragraphs[0]` |
| `body/p[3]/hyperlink[0]/r[0]` | XML `w:hyperlink` → `w:r` |
| `header[0]/p[1]` | `section.header.paragraphs[1]` |
| `footer[0]/p[0]` | `section.footer.paragraphs[0]` |

## 4. Pemetaan run_index
- `run_index` adalah indeks dalam `paragraph.runs` pada snapshot.
- Untuk hyperlink, `run_index` adalah indeks dalam `w:hyperlink/w:r`.
- Untuk tabel bersarang, indeks dihitung pada level paragraf sel.

## 5. Pemetaan char_start/char_end
- Offset dihitung dari `run.text` pada snapshot.
- Untuk hyperlink, offset dihitung dari teks dalam `w:hyperlink`.
- `global_text_offset` opsional: offset dalam teks gabungan blok, untuk UI.

## 6. Snapshot dan Stale Check
- Setiap analisis menghasilkan `snapshot_id` unik.
- Sebelum apply:
  1. Ambil teks saat ini pada lokasi.
  2. Bandingkan dengan `original_value`.
  3. Bandingkan `hash(snapshot)` dengan `original_text_hash`.
  4. Jika berbeda → `application_status = stale`.
- Stale check dilakukan per finding, bukan global.

## 7. Overlap
- Dua finding overlap jika rentang `[char_start, char_end]` pada run/block yang sama beririsan.
- Jika overlap:
  - `review_status = conflict`.
  - Tidak diterapkan otomatis.
  - UI menampilkan pilihan ke pengguna.
- Overlap antar block tidak dianggap konflik.

## 8. Apply Order
- Urutkan finding yang disetujui berdasarkan `global_text_offset` **menurun** (dari offset terbesar).
- Alasan: perubahan pada offset besar tidak menggeser offset kecil.
- Setelah setiap apply, update offset finding lain di blok yang sama.
- Jika apply gagal, lanjut ke finding berikutnya, tandai `failed`.

## 9. Contoh: Paragraf

block_path = body/p[3]
run_index = 0
char_start = 5, char_end = 11
original_value = "disini"
suggested_value = "di sini"


## 10. Contoh: Tabel Bersarang

block_path = body/table[0]/row[1]/cell[2]/table[0]/row[0]/cell[0]/p[0]

Resolusi: `document.tables[0].rows[1].cells[2].tables[0].rows[0].cells[0].paragraphs[0]`.

## 11. Contoh: Hyperlink

block_path = body/p[5]/hyperlink[0]/r[0]
Resolusi: `document.paragraphs[5]._element.findall(qn('w:hyperlink'))[0].findall(qn('w:r'))[0]`.

## 12. Contoh: Multilevel List
block_path = body/p[7]
pPr/numPr/ilvl = 1, numId = 3
Edit teks tidak mengubah `numPr`. Format list diubah hanya jika finding format disetujui.

## 13. Kasus Gagal
| Kasus | Aksi |
|---|---|
| Path tidak resolve | `application_status = failed`. |
| Run index di luar batas | `stale` atau `failed`. |
| Hash berbeda | `stale`. |
| Overlap | `conflict`. |
| Fitur tidak didukung | `skipped`. |

## 14. DECISION
- DECISION-004: Apply order dari offset terbesar. **Status: FINAL.**
- DECISION-005: Overlap → `conflict`, tidak otomatis. **Status: FINAL.**
- DECISION-006: Stale check per finding dengan hash. **Status: FINAL.**
