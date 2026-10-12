"""DocxLint — UI Streamlit Phase 2.

Fitur: upload, validasi, baca struktur, ekspor round-trip.
Belum ada: pemeriksaan ejaan, tanda baca, italic, atau format.
"""

import sys
from pathlib import Path

import streamlit as st

# Pastikan `src` dapat diimpor saat Streamlit dijalankan dari root proyek.
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.docxlint.services.docx_reader import read_document  # noqa: E402
from src.docxlint.services.docx_validator import DocxValidator  # noqa: E402
from src.docxlint.services.docx_writer import export_roundtrip  # noqa: E402
from src.docxlint.services.network_guard import network_guard  # noqa: E402
from src.docxlint.utils.errors import ValidationError  # noqa: E402


st.set_page_config(page_title="DocxLint", page_icon="📄", layout="wide")

st.title("DocxLint")
st.caption("Alat pemeriksaan DOCX lokal. Phase 2: validasi, baca, dan ekspor.")

st.warning(
    "Phase 2 belum memeriksa ejaan, tanda baca, atau format. "
    "Fitur tersebut akan hadir di fase berikutnya."
)

uploaded = st.file_uploader("Unggah file .docx", type=["docx"])

if uploaded is None:
    st.info("Silakan unggah file DOCX untuk memulai.")
    st.stop()

data = uploaded.read()
filename = uploaded.name
validator = DocxValidator()

try:
    with network_guard():
        validator.validate(data, filename)
        snapshot = read_document(data)
except ValidationError as exc:
    st.error(f"Validasi gagal: {exc}")
    st.stop()
except Exception:
    # Jangan tampilkan detail yang bisa membocorkan isi dokumen.
    st.error("Terjadi kesalahan saat memproses dokumen.")
    st.stop()

st.success("File valid dan berhasil dibaca.")

body_blocks = snapshot.parts.get("document", [])
para_count = sum(
    1 for b in body_blocks if b.block_type in {"paragraph", "heading", "list_item"}
)
table_blocks = [
    b for b in body_blocks if "/table[" in b.block_path
]
table_cells = {"/".join(b.block_path.split("/")[:5]) for b in table_blocks}

col1, col2, col3, col4 = st.columns(4)
col1.metric("Nama file", filename)
col2.metric("Ukuran", f"{len(data) / 1024:.1f} KB")
col3.metric("Paragraf", para_count)
col4.metric("Sel tabel", len(table_cells))

with st.expander("Pratinjau struktur dokumen", expanded=False):
    for part_name, blocks in snapshot.parts.items():
        st.markdown(f"**Bagian `{part_name}`** — {len(blocks)} blok")
        for block in blocks[:200]:
            complex_count = sum(1 for r in block.runs if r.is_complex_run)
            marker = f" ⚠️ {complex_count} run kompleks" if complex_count else ""
            preview = block.text[:120].replace("\n", " ")
            st.text(
                f"{block.block_path} [{block.block_type}]{marker}: {preview}"
            )
        if len(blocks) > 200:
            st.caption(f"… {len(blocks) - 200} blok lainnya tidak ditampilkan.")

st.divider()
st.subheader("Ekspor")
st.caption(
    "Unduhan saat ini mengembalikan byte DOCX asli (round-trip). "
    "Belum ada perubahan yang diterapkan."
)

exported = export_roundtrip(data)
st.download_button(
    label="Unduh DOCX (round-trip)",
    data=exported,
    file_name=f"roundtrip_{filename}",
    mime=(
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document"
    ),
)

st.caption(
    "Mode lokal: tidak ada konten dokumen yang dikirim ke layanan eksternal."
)