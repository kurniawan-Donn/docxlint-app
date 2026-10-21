# Glossary — Format dan Contoh

## File
`config/terminology.csv` (UTF-8, no BOM, header wajib).

## Kolom
| Kolom | Wajib | Deskripsi |
|---|---|---|
| `term` | Ya | Satu kata atau frasa multi-kata. |
| `italic` | Ya | `true`/`false`. Ekspektasi italic. |
| `category` | Ya | mis. `istilah_asing`, `akronim`, `nama_produk`. |
| `note` | Ya (boleh kosong) | Catatan bebas. |
| `language` | Tidak | Kode bahasa, mis. `en`, `id`. |
| `case_sensitive` | Tidak | `true` untuk match case-sensitive. Default `false`. |
| `priority` | Tidak | Integer, makin besar makin diprioritaskan saat overlap. Default `0`. |

Kolom opsional adalah **extension Phase 4**. File Phase 1.6 tanpa kolom ini tetap valid.

## Contoh
```csv
term,italic,category,note,language,case_sensitive,priority
machine learning,true,istilah_asing,gunakan italic,en,false,10
API,false,akronim,jangan italic,,true,10
Streamlit,false,nama_produk,jangan italic,,true,10