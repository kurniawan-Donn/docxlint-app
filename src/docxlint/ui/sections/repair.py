"""Stage 4 — Rencana perubahan & perbaikan.

Logika build/validate/apply dipindah apa adanya dari `app.py` (Phase 6/7).
Yang baru: tabel change plan, card konfirmasi, ringkasan hasil.
"""

import streamlit as st

from ...models.change_plan import (
    FAILED,
    OPERATION_APPLY_ITALIC,
    OPERATION_REPLACE_TEXT,
)
from ...services.docx_repair import RepairEngine
from ...services.invalidation import is_change_plan_valid
from ...services.output_validator import validate_output
from ..components import (
    change_plan_table_html,
    render_empty_state,
    render_error_banner,
    render_metric_row,
    render_success_banner,
    render_warning_banner,
)

DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.document"
)


def render_repair_section(combined, snapshot, original_bytes, filename):
    st.subheader("Rencana Perubahan & Perbaikan")
    st.caption(
        "Perbaikan hanya diterapkan ke **salinan** dokumen. "
        "File asli tidak pernah ditimpa."
    )

    state = st.session_state.get("selection_state")
    current_profile_id = st.session_state.get("current_profile_id", "")
    current_config_hash = st.session_state.get("current_config_hash", "")
    if state is None or not state.selected_ids:
        render_empty_state(
            "Belum ada temuan yang dipilih",
            "Pilih temuan di tab Tinjauan terlebih dahulu.",
        )
        return

    selected = [f for f in combined if f.finding_id in state.selected_ids]

    # Bangun approved actions
    approved: dict = {}
    for f in selected:
        if f.category == "spelling":
            approved[f.finding_id] = {
                "operation": OPERATION_REPLACE_TEXT,
                "replacement": st.session_state.get(f"sug_{f.finding_id}")
                    or f.suggested_value,
            }
        elif f.category == "italic_formatting":
            expected = f.metadata.get("expected_italic")
            if expected is True:
                approved[f.finding_id] = {
                    "operation": OPERATION_APPLY_ITALIC,
                    "replacement": None,
                }

    if not approved:
        render_warning_banner(
            "Tidak ada temuan yang didukung untuk perbaikan otomatis",
            "Hanya temuan ejaan dengan saran dan isu italic dengan "
            "ekspektasi italic=true yang didukung.",
        )
        return

    engine = RepairEngine(original_bytes, snapshot)
    plan = engine.build_change_plan(selected, approved)
    engine.validate_plan(plan)
    # Phase 7: isi metadata profil di plan dan tolak jika sudah berubah.
    plan.profile_id = current_profile_id
    plan.profile_version = st.session_state.get(
        "active_profile_version", ""
    )
    plan.config_hash = current_config_hash

    valid_plan, reason = is_change_plan_valid(
        plan, current_profile_id, current_config_hash,
    )
    if not valid_plan:
        render_error_banner(
            "Rencana perubahan tidak valid",
            f"Konfigurasi berubah ({reason}). Jalankan ulang analisis "
            "sebelum menerapkan perubahan.",
        )
        return
    counts = plan.counts()

    render_metric_row([
        ("Direncanakan", counts["planned"]),
        ("Valid", counts["valid"]),
        ("Konflik", counts["conflict"]),
        ("Tidak didukung", counts["unsupported"] + counts["stale"]
         + counts["rejected"]),
    ])

    st.markdown("**Pratinjau rencana perubahan**")
    st.markdown(change_plan_table_html(plan.items), unsafe_allow_html=True)

    st.write("")
    with st.container(border=True, key="repair_confirm_card"):
        render_warning_banner(
            "Konfirmasi sebelum menerapkan",
            f"{counts['valid']} perubahan valid akan diterapkan ke salinan "
            "dokumen. Item yang tidak valid dilewati. Dokumen asli tidak "
            "diubah.",
        )
        confirm = st.checkbox(
            "Saya mengonfirmasi akan menerapkan perubahan yang valid ke "
            "salinan dokumen. Saya memahami dokumen asli tidak diubah.",
            key="repair_confirm",
        )
        apply_clicked = st.button(
            "Terapkan Perubahan", type="primary", disabled=not confirm,
            help="Aktif setelah kotak konfirmasi dicentang.",
        )

    if apply_clicked:
        with st.spinner("Menerapkan perubahan…"):
            out_bytes, plan = engine.apply_plan(plan)
            report = validate_output(out_bytes, plan)
        st.session_state["repair_output_bytes"] = out_bytes
        st.session_state["repair_plan"] = plan
        st.session_state["repair_report"] = report

    if "repair_output_bytes" in st.session_state:
        plan = st.session_state["repair_plan"]
        report = st.session_state["repair_report"]
        counts = plan.counts()

        st.markdown("**Hasil perbaikan**")
        render_metric_row([
            ("Diterapkan", counts["applied"]),
            ("Dilewati", counts["skipped"]),
            ("Gagal", counts["failed"]),
            ("Belum diproses", counts["not_applied"]),
        ])

        failed = [i for i in plan.items if i.execution == FAILED]
        if failed:
            with st.expander(f"Daftar gagal ({len(failed)})"):
                st.markdown(change_plan_table_html(failed,
                                                   use_execution=True),
                            unsafe_allow_html=True)

        if not report.ok:
            render_error_banner(
                "Validasi output gagal",
                f"{report.reason}. Rollback ke byte asli.",
            )

        critical = engine.has_critical_failure(plan)
        st.session_state["repair_critical"] = critical
        if critical:
            render_error_banner(
                "Unduhan perbaikan diblokir",
                "Terdapat kegagalan kritis (body/header/footer/tabel) — "
                "DECISION-014/024.",
            )

        if report.ok and not critical:
            render_success_banner(
                "Validasi output berhasil",
                "Salinan hasil perbaikan siap diunduh.",
            )
            st.download_button(
                label="Unduh DOCX hasil perbaikan",
                data=st.session_state["repair_output_bytes"],
                file_name=f"repaired_{filename}",
                mime=DOCX_MIME,
                key="dl_repaired",
                type="primary",
            )
