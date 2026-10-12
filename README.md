# DocxLint — Phase 2

Alat pemeriksaan DOCX **local-first**. Phase 2 menyediakan fondasi:
unggah, validasi, baca struktur, dan ekspor round-trip.

## Lingkup Phase 2
**Sudah ada**
- UI Streamlit dasar (Bahasa Indonesia).
- Validasi file DOCX (ukuran, ZIP, komponen, makro, path traversal).
- Pembacaan paragraf, tabel, header/footer, style, deteksi run kompleks.
- Ekspor round-trip (byte identik).
- Network guard di mode lokal.
- Test `pytest` untuk layanan inti.

**Belum ada**
- Deteksi typo, ejaan, tanda baca, kata berulang.
- Deteksi istilah Inggris dan italic otomatis.
- Perbaikan format (font, ukuran, margin, spasi, indentasi, alignment).
- Edit selektif pada DOCX (writer masih no-op).
- Rollback berbasis bytes (akan datang di Phase 4).

## Persyaratan
- Python 3.10+
- Windows, Linux, atau macOS

## Instalasi

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt