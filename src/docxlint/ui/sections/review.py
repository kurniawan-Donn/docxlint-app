"""Stage 3 — Tinjauan temuan.

Logika seleksi/filter dipindah apa adanya dari `app.py` (Phase 5):
key widget `sel_*`, `rs_*`, `flt_*` dan `SelectionState` tidak berubah.
Untuk mengurangi kebisingan, tampilan dibagi menjadi "Perlu tindakan" vs
"Informasi", temuan dengan kata yang sama dapat dikelompokkan, dan daftar
dipaginasi. `SelectionState.selected_ids` tetap satu-satunya sumber
kebenaran pilihan.
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
    format_location,
    render_empty_state,
    render_finding_card,
    render_metric_row,
    severity_label,
)
from ..review_view import (
    PER_PAGE,
    SCOPE_ACTIONABLE,
    SCOPE_ALL,
    SCOPE_INFO,
    VIEW_FLAT,
    VIEW_GROUPED,
    filter_scope,
    group_findings,
    page_range_text,
    paginate,
    sort_by_priority,
)

REVIEW_OPTIONS = ["pending", "accepted", "rejected", "conflict"]
_WIDGET_PREFIXES = ("sel_", "rs_", "grp_", "rsg_")


# --- callbacks (dijalankan Streamlit sebelum rerun) ------------------------

def _reset_page() -> None:
    st.session_state["rv_page"] = 1


def _shift_page(delta: int) -> None:
    st.session_state["rv_page"] = int(st.session_state.get("rv_page", 1)) + delta


def _on_group_toggle(group_key: str, members: list) -> None:
    state: SelectionState = st.session_state["selection_state"]
    checked = bool(st.session_state.get(group_key))
    for f in members:
        if checked and is_selectable(f):
            state.selected_ids.add(f.finding_id)
        elif not checked:
            state.selected_ids.discard(f.finding_id)
        st.session_state.pop(f"sel_{f.finding_id}", None)


def _on_group_status(status_key: str, members: list) -> None:
    new_status = st.session_state.get(status_key, REVIEW_PENDING)
    for f in members:
        f.review_status = new_status
        st.session_state.pop(f"rs_{f.finding_id}", None)


def _sanitize_multi(key: str, options) -> None:
    """Buang nilai filter yang tidak lagi ada di opsi (mis. setelah
    pemeriksaan dijalankan ulang) agar widget tidak error."""
    value = st.session_state.get(key)
    if value:
        allowed = set(options)
        st.session_state[key] = [v for v in value if v in allowed]


# --- render ----------------------------------------------------------------

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
            if k.startswith(_WIDGET_PREFIXES):
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

    actionable = filter_scope(findings, SCOPE_ACTIONABLE)
    informational = filter_scope(findings, SCOPE_INFO)
    summary = summarize(findings, state.selected_ids)

    render_metric_row(
        [
            ("Total temuan", summary["total"]),
            ("Perlu tindakan", len(actionable)),
            ("Informasi", len(informational)),
            ("Dipilih", summary["selected"]),
        ],
        helps=[
            None,
            "Dapat diperbaiki otomatis: ejaan dengan saran, atau italic "
            "pada istilah terdaftar.",
            "Tidak diperbaiki otomatis: kata tidak dikenal, istilah asing, "
            "kandidat belum pasti.",
            None,
        ],
    )
    with st.expander("Rincian per kategori"):
        render_metric_row([
            ("Kemungkinan salah eja", summary["spelling"]),
            ("Kata tidak dikenal", summary["unknown_word"]),
            ("Istilah asing", summary["foreign_term"]),
        ])
        render_metric_row(
            [
                ("Isu italic", summary["italic_formatting"]),
                ("Belum pasti", summary["uncertain"]),
                ("Dilewati", summary["skipped"]),
            ],
            helps=[None, "Confidence di bawah 0,85.",
                   "Run kompleks yang tidak diforsir (DECISION-021)."],
        )

    scope_counts = {
        SCOPE_ACTIONABLE: len(actionable),
        SCOPE_INFO: len(informational),
        SCOPE_ALL: len(findings),
    }
    scope_labels = {
        SCOPE_ACTIONABLE: "Perlu tindakan",
        SCOPE_INFO: "Informasi",
        SCOPE_ALL: "Semua",
    }

    with st.container(key="review_filter_bar"):
        v1, v2, v3 = st.columns([0.45, 0.25, 0.30],
                                vertical_alignment="bottom")
        with v1:
            scope = st.segmented_control(
                "Lingkup",
                options=[SCOPE_ACTIONABLE, SCOPE_INFO, SCOPE_ALL],
                format_func=lambda x: f"{scope_labels[x]} ({scope_counts[x]})",
                default=SCOPE_ACTIONABLE,
                key="rv_scope",
                on_change=_reset_page,
                help="Perlu tindakan = temuan yang dapat diperbaiki otomatis.",
            ) or SCOPE_ACTIONABLE
        with v2:
            view = st.segmented_control(
                "Tampilan",
                options=[VIEW_GROUPED, VIEW_FLAT],
                format_func=lambda x: "Per kata" if x == VIEW_GROUPED
                else "Per temuan",
                default=VIEW_GROUPED,
                key="rv_view",
                on_change=_reset_page,
                help="Per kata menggabungkan temuan dengan kata dan saran "
                     "yang sama menjadi satu card.",
            ) or VIEW_GROUPED
        with v3:
            f_sel = st.segmented_control(
                "Pilihan",
                options=["all", "selected", "unselected"],
                format_func=lambda x: SELECTION_LABELS[x],
                default="all",
                key="flt_sel",
                on_change=_reset_page,
            ) or "all"

        scoped = filter_scope(findings, scope)
        all_categories = sorted({f.category for f in scoped})
        all_severities = sorted({f.severity for f in scoped})
        all_review = sorted({f.review_status for f in scoped})
        all_app = sorted({f.application_status for f in scoped})
        _sanitize_multi("flt_cat", all_categories)
        _sanitize_multi("flt_sev", all_severities)
        _sanitize_multi("flt_rev", all_review)
        _sanitize_multi("flt_app", all_app)

        s1, s2 = st.columns([0.75, 0.25], vertical_alignment="bottom")
        with s1:
            f_search = st.text_input(
                "Cari temuan",
                key="flt_search",
                placeholder="Kata, saran, rule_id, atau alasan",
                on_change=_reset_page,
            )
        with s2:
            with st.popover("Filter lanjutan"):
                f_rev = st.multiselect(
                    "Status tinjauan", all_review, key="flt_rev",
                    format_func=lambda x: REVIEW_STATUS_LABELS.get(x, x),
                    on_change=_reset_page,
                )
                f_app = st.multiselect(
                    "Status aplikasi", all_app, key="flt_app",
                    format_func=lambda x: APPLICATION_STATUS_LABELS.get(x, x),
                    on_change=_reset_page,
                )
        c1, c2, c3 = st.columns([0.45, 0.28, 0.27])
        with c1:
            f_cat = st.pills(
                "Kategori", all_categories, selection_mode="multi",
                format_func=category_label, key="flt_cat",
                on_change=_reset_page,
            )
        with c2:
            f_sev = st.pills(
                "Severity", all_severities, selection_mode="multi",
                format_func=severity_label, key="flt_sev",
                on_change=_reset_page,
            )
        with c3:
            f_conf = st.pills(
                "Confidence", ["high", "medium", "low"],
                selection_mode="multi",
                format_func=lambda x: CONFIDENCE_LABELS[x][0],
                key="flt_conf",
                on_change=_reset_page,
                help="Yakin ≥ 0,85 · Cukup yakin ≥ 0,60 · Ragu < 0,60",
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

    visible = filter_findings(scoped, filters, state.selected_ids)
    units = (
        group_findings(visible) if view == VIEW_GROUPED
        else sort_by_priority(visible)
    )

    # Clamp halaman sebelum widget halaman dibuat.
    _, page, total_pages = paginate(units, st.session_state.get("rv_page", 1))
    st.session_state["rv_page"] = page
    page_items, _, _ = paginate(units, page)

    t1, t2, t3, t4 = st.columns([0.4, 0.2, 0.2, 0.2],
                                vertical_alignment="center")
    unit_text = (
        f" dalam **{len(units)}** kelompok" if view == VIEW_GROUPED else ""
    )
    t1.markdown(
        f"Menampilkan **{len(visible)}** dari **{len(findings)}** "
        f"temuan{unit_text} · Dipilih: **{len(state.selected_ids)}**"
    )
    with t2:
        if st.button("Pilih yang terlihat", use_container_width=True,
                     help="Pilih semua temuan yang lolos filter, di semua "
                          "halaman."):
            for f in visible:
                if is_selectable(f):
                    state.selected_ids.add(f.finding_id)
                    st.session_state[f"sel_{f.finding_id}"] = True
            st.rerun()
    with t3:
        if st.button("Batalkan yang terlihat", use_container_width=True,
                     help="Batalkan pilihan pada temuan yang lolos filter, "
                          "di semua halaman."):
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
        if scope == SCOPE_ACTIONABLE and not actionable:
            render_empty_state(
                "Tidak ada temuan yang bisa diperbaiki otomatis",
                f"Ada {len(informational)} temuan informasi. Pilih lingkup "
                "Informasi untuk melihatnya.",
            )
        else:
            render_empty_state(
                "Tidak ada temuan yang cocok dengan filter",
                "Kosongkan pencarian atau kurangi chip kategori, severity, "
                "dan confidence yang aktif.",
            )
        return

    for unit in page_items:
        if view == VIEW_GROUPED:
            _render_group_card(unit, state)
        else:
            _render_flat_card(unit, state)

    if total_pages > 1:
        p1, p2, p3 = st.columns([0.25, 0.5, 0.25],
                                vertical_alignment="center")
        with p1:
            st.button("‹ Sebelumnya", disabled=page <= 1,
                      on_click=_shift_page, args=(-1,),
                      use_container_width=True, key="rv_prev")
        with p2:
            st.markdown(
                f"<div style='text-align:center'>Halaman {page} dari "
                f"{total_pages} · {page_range_text(page, PER_PAGE, len(units))}"
                "</div>",
                unsafe_allow_html=True,
            )
        with p3:
            st.button("Berikutnya ›", disabled=page >= total_pages,
                      on_click=_shift_page, args=(1,),
                      use_container_width=True, key="rv_next")


def _render_flat_card(f, state: SelectionState) -> None:
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
            current = f.review_status if f.review_status in REVIEW_OPTIONS \
                else REVIEW_PENDING
            new_status = st.radio(
                "Status tinjauan",
                options=REVIEW_OPTIONS,
                index=REVIEW_OPTIONS.index(current),
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


def _render_group_card(group, state: SelectionState) -> None:
    members = group.items
    if group.count == 1:
        _render_flat_card(group.lead, state)
        return

    selectable = [f for f in members if is_selectable(f)]
    grp_key = f"grp_{group.group_id}"
    # Nilai checkbox kelompok diturunkan dari selected_ids (sumber kebenaran).
    st.session_state[grp_key] = bool(selectable) and all(
        f.finding_id in state.selected_ids for f in selectable
    )
    n_selected = sum(1 for f in members if f.finding_id in state.selected_ids)

    statuses = {f.review_status for f in members}
    mixed_status = len(statuses) > 1
    status_key = f"rsg_{group.group_id}"
    common = REVIEW_PENDING if mixed_status else next(iter(statuses))
    st.session_state[status_key] = common if common in REVIEW_OPTIONS \
        else REVIEW_PENDING

    with st.container(border=True, key=f"fcard_g{group.group_id}"):
        render_finding_card(group.lead, occurrences=group.count)
        a1, a2, a3 = st.columns([0.22, 0.48, 0.30],
                                vertical_alignment="center")
        with a1:
            st.checkbox(
                f"Pilih semua ({group.count})",
                key=grp_key,
                disabled=not selectable,
                on_change=_on_group_toggle, args=(grp_key, members),
                help=(
                    f"{n_selected} dari {group.count} lokasi dipilih."
                    if selectable else
                    "Temuan konflik/dilewati tidak dapat dipilih."
                ),
            )
        with a2:
            st.radio(
                "Status tinjauan kelompok",
                options=REVIEW_OPTIONS,
                format_func=lambda x: REVIEW_STATUS_LABELS[x],
                horizontal=True,
                key=status_key,
                label_visibility="collapsed",
                on_change=_on_group_status, args=(status_key, members),
                help="Mengubah status semua lokasi dalam kelompok ini.",
            )
        with a3:
            with st.expander(f"Lokasi ({group.count})"):
                lines = []
                for f in members:
                    loc = f.location
                    mark = "✓ " if f.finding_id in state.selected_ids else ""
                    lines.append(
                        f"- {mark}`"
                        + format_location(loc.block_path, loc.run_index,
                                          loc.char_start, loc.char_end)
                        + "`"
                    )
                st.markdown("\n".join(lines))
        notes = []
        if mixed_status:
            notes.append("Status tinjauan berbeda-beda di dalam kelompok.")
        if 0 < n_selected < group.count:
            notes.append(f"{n_selected} dari {group.count} lokasi dipilih.")
        if notes:
            st.caption(" ".join(notes))
