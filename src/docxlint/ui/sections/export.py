"""Stage 5 — Ekspor: round-trip dan hasil perbaikan."""

import streamlit as st

from ...services.docx_writer import export_roundtrip
from ...services.network_guard import network_guard
from ..components import (
    render_empty_state,
    render_error_banner,
    repair_state,
)
from .repair import DOCX_MIME


def render_export_section(original_bytes, filename) -> None:
    st.subheader("Ekspor")

    with st.container(border=True):
        st.markdown("#### Salinan round-trip")
        st.caption(
            "Byte DOCX asli dikembalikan apa adanya (byte identik). "
            "Berguna untuk memastikan dokumen tidak berubah."
        )
        with network_guard():
            roundtrip = export_roundtrip(original_bytes)
        st.download_button(
            label="Unduh DOCX (round-trip)",
            data=roundtrip,
            file_name=f"roundtrip_{filename}",
            mime=DOCX_MIME,
            key="dl_roundtrip",
        )

    with st.container(border=True):
        st.markdown("#### Hasil perbaikan")
        s = repair_state(st.session_state)
        if s == "repair_none":
            render_empty_state(
                "Belum ada hasil perbaikan",
                "Terapkan perubahan di tab Perbaikan terlebih dahulu.",
            )
        elif s == "repair_blocked":
            render_error_banner(
                "Unduhan perbaikan diblokir",
                "Validasi output gagal atau ada kegagalan kritis. Lihat "
                "detail di tab Perbaikan.",
            )
        else:
            st.caption("Validasi output lolos dan tidak ada kegagalan kritis.")
            st.download_button(
                label="Unduh DOCX hasil perbaikan",
                data=st.session_state["repair_output_bytes"],
                file_name=f"repaired_{filename}",
                mime=DOCX_MIME,
                key="dl_repaired_export",
                type="primary",
            )

    st.caption(
        "Mode lokal: konten dokumen tidak dikirim ke layanan eksternal."
    )
