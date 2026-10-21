"""Stage 3 — Tinjauan temuan.

Logika seleksi/filter dipindah apa adanya dari `app.py` (Phase 5):
key widget `sel_*`, `rs_*`, `flt_*` dan `SelectionState` tidak berubah.
Yang baru hanya wadah visual (filter bar, card, toolbar).
"""

import streamlit as st

from ...models.finding import REVIEW_PENDING
from ...services.review_state import (
    ReviewFilters,
    SelectionState,
    filter_findings,
    is_selectable,
    summarize,
)
from ..components import (
    APPLICATION_STATUS_LABELS,
    CONFIDENCE_LABELS,
    REVIEW_STATUS_LABELS,
    SELECTION_LABELS,
    category_label,
    render_empty_state,
    render_finding_card,
    render_metric_row,
    severity_label,
)

MAX_VISIBLE = 500


def render_review_section(findings, snapshot) -> None:
    st.subheader("Tinjau Temuan")
    st.caption(
        "Memilih temuan TIDAK mengubah dokumen. Perubahan baru diterapkan "
        "di tab Perbaikan setelah Anda mengonfirmasi."
    )

    if "selection_state" not in st.session_state:
        st.session_state["selection_state"] = SelectionState()
    state: SelectionState = st.session_state["selection_state"]

    snapshot_id = snapshot.snapshot_id
    changed = state.ensure_snapshot(snapshot_id)
    if changed:
        # Bersihkan widget state lama yang sudah tidak relevan.
        for k in list(st.session_state.keys()):
            if k.startswith("sel_") or k.startswith("rs_"):
                del st.session_state[k]

    # Sinkronkan dari nilai checkbox rerun ini agar metrik dan hitungan
    # "Dipilih" tidak tertinggal satu rerun.
    for f in findings:
        sel_key = f"sel_{f.finding_id}"
        if sel_key in st.session_state:
            if st.session_state[sel_key] and is_selectable(f):
                state.selected_ids.add(f.finding_id)
            elif not st.session_state[sel_key]:
                state.selected_ids.discard(f.finding_id)

    summary = summarize(findings, state.selected_ids)

    render_metric_row([
        ("Total temuan", summary["total"]),
        ("Kemungkinan salah eja", summary["spelling"]),
        ("Kata tidak dikenal", summary["unknown_word"]),
        ("Dipilih", summary["selected"]),
    ])
    render_metric_row(
        [
            ("Istilah asing", summary["foreign_term"]),
            ("Isu italic", summary["italic_formatting"]),
            ("Belum pasti", summary["uncertain"]),
            ("Dilewati", summary["skipped"]),
        ],
        helps=[None, None, "Confidence di bawah 0,85.",
               "Run kompleks yang tidak diforsir (DECISION-021)."],
    )

    all_categories = sorted({f.category for f in findings})
    all_severities = sorted({f.severity for f in findings})
    all_review = sorted({f.review_status for f in findings})
    all_app = sorted({f.application_status for f in findings})

    with st.container(key="review_filter_bar"):
        s1, s2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
        with s1:
            f_search = st.text_input(
                "Cari temuan",
                key="flt_search",
                placeholder="Kata, saran, rule_id, atau alasan",
            )
        with s2:
            f_sel = st.segmented_control(
                "Tampilkan",
                options=["all", "selected", "unselected"],
                format_func=lambda x: SELECTION_LABELS[x],
                default="all",
                key="flt_sel",
            ) or "all"
        c1, c2, c3 = st.columns([0.45, 0.28, 0.27])
        with c1:
            f_cat = st.pills(
                "Kategori", all_categories, selection_mode="multi",
                format_func=category_label, key="flt_cat",
            )
        with c2:
            f_sev = st.pills(
                "Severity", all_severities, selection_mode="multi",
                format_func=severity_label, key="flt_sev",
            )
        with c3:
            f_conf = st.pills(
                "Confidence", ["high", "medium", "low"],
                selection_mode="multi",
                format_func=lambda x: CONFIDENCE_LABELS[x][0],
                key="flt_conf",
                help="Yakin ≥ 0,85 · Cukup yakin ≥ 0,60 · Ragu < 0,60",
            )
        with st.popover("Filter lanjutan"):
            f_rev = st.multiselect(
                "Status tinjauan", all_review, key="flt_rev",
                format_func=lambda x: REVIEW_STATUS_LABELS.get(x, x),
            )
            f_app = st.multiselect(
                "Status aplikasi", all_app, key="flt_app",
                format_func=lambda x: APPLICATION_STATUS_LABELS.get(x, x),
            )

    filters = ReviewFilters(
        categories=set(f_cat or []),
        severities=set(f_sev or []),
        review_statuses=set(f_rev),
        application_statuses=set(f_app),
        confidence_bands=set(f_conf or []),
        selection=f_sel,
        search_text=f_search,
    )

    visible = filter_findings(findings, filters, state.selected_ids)

    t1, t2, t3, t4 = st.columns([0.4, 0.2, 0.2, 0.2],
                                vertical_alignment="center")
    t1.markdown(
        f"Menampilkan **{len(visible)}** dari **{len(findings)}** temuan · "
        f"Dipilih: **{len(state.selected_ids)}**"
    )
    with t2:
        if st.button("Pilih yang terlihat", use_container_width=True,
                     help="Pilih semua temuan yang lolos filter."):
            for f in visible:
                if is_selectable(f):
                    state.selected_ids.add(f.finding_id)
                    st.session_state[f"sel_{f.finding_id}"] = True
            st.rerun()
    with t3:
        if st.button("Batalkan yang terlihat", use_container_width=True,
                     help="Batalkan pilihan pada temuan yang lolos filter."):
            for f in visible:
                state.selected_ids.discard(f.finding_id)
                st.session_state[f"sel_{f.finding_id}"] = False
            st.rerun()
    with t4:
        if st.button("Bersihkan pilihan", use_container_width=True,
                     help="Hapus semua pilihan, termasuk yang tersembunyi."):
            state.selected_ids.clear()
            for k in list(st.session_state.keys()):
                if k.startswith("sel_"):
                    st.session_state[k] = False
            st.rerun()

    if not visible:
        render_empty_state(
            "Tidak ada temuan yang cocok dengan filter",
            "Kosongkan pencarian atau kurangi chip kategori, severity, "
            "dan confidence yang aktif.",
        )
        return

    options = ["pending", "accepted", "rejected", "conflict"]
    for f in visible[:MAX_VISIBLE]:
        sel_key = f"sel_{f.finding_id}"
        if sel_key not in st.session_state:
            st.session_state[sel_key] = f.finding_id in state.selected_ids

        with st.container(border=True, key=f"fcard_{f.finding_id}"):
            render_finding_card(f)
            a1, a2, a3 = st.columns([0.16, 0.54, 0.30],
                                    vertical_alignment="center")
            with a1:
                selectable = is_selectable(f)
                checked = st.checkbox(
                    "Pilih",
                    key=sel_key,
                    disabled=not selectable,
                    help=None if selectable else
                    "Temuan konflik/dilewati tidak dapat dipilih.",
                )
                if checked:
                    state.selected_ids.add(f.finding_id)
                else:
                    state.selected_ids.discard(f.finding_id)
            with a2:
                status_key = f"rs_{f.finding_id}"
                current = f.review_status if f.review_status in options \
                    else REVIEW_PENDING
                new_status = st.radio(
                    "Status tinjauan",
                    options=options,
                    index=options.index(current),
                    format_func=lambda x: REVIEW_STATUS_LABELS[x],
                    horizontal=True,
                    key=status_key,
                    label_visibility="collapsed",
                )
                if new_status != f.review_status:
                    f.review_status = new_status
            with a3:
                with st.expander("Detail"):
                    st.markdown(
                        f"- Rule: `{f.rule_id}`\n"
                        f"- Kategori: `{f.category}`\n"
                        f"- Confidence: `{f.confidence:.2f}`\n"
                        f"- Status aplikasi: "
                        f"{APPLICATION_STATUS_LABELS.get(f.application_status, f.application_status)}\n"
                        f"- ID: `{f.finding_id[:12]}`"
                    )

    if len(visible) > MAX_VISIBLE:
        st.caption(
            f"… {len(visible) - MAX_VISIBLE} temuan lainnya tidak "
            "ditampilkan. Persempit filter untuk melihatnya."
        )
