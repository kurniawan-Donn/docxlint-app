"""Komponen UI DocxLint (Phase 7.5).

Bagian atas: helper murni (tanpa Streamlit, dapat ditest).
Bagian bawah: fungsi `render_*` yang memanggil Streamlit.

Semua teks yang berasal dari dokumen di-escape sebelum masuk HTML.
"""

from dataclasses import dataclass
from html import escape
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

from ..services.review_state import confidence_band
from .theme import COLORS

# ---------------------------------------------------------------------------
# Label & metadata (murni)
# ---------------------------------------------------------------------------

# tone, ikon (bukan emoji), label
SEVERITY_META = {
    "high": ("danger", "▲", "Tinggi"),
    "medium": ("warning", "◆", "Sedang"),
    "low": ("accent", "●", "Rendah"),
    "info": ("muted", "○", "Info"),
}

_TONE_TEXT_COLOR = {
    "danger": COLORS["danger_text"],
    "warning": COLORS["warning_text"],
    "accent": COLORS["accent"],
    "success": COLORS["success_text"],
    "muted": COLORS["muted_text"],
    "neutral": COLORS["text"],
}

CATEGORY_LABELS = {
    "spelling": "Salah eja",
    "unknown_word": "Kata tidak dikenal",
    "foreign_term": "Istilah asing",
    "italic_formatting": "Italic",
    "formatting": "Format",
}

CONFIDENCE_LABELS = {
    "high": ("Yakin", "success", "✓"),
    "medium": ("Cukup yakin", "warning", "~"),
    "low": ("Ragu", "danger", "?"),
}

REVIEW_STATUS_LABELS = {
    "pending": "Menunggu",
    "accepted": "Diterima",
    "rejected": "Ditolak",
    "conflict": "Konflik",
}

APPLICATION_STATUS_LABELS = {
    "not_applied": "Belum diterapkan",
    "applied": "Diterapkan",
    "failed": "Gagal",
    "skipped": "Dilewati",
    "stale": "Kedaluwarsa",
    "conflict": "Konflik",
}

SELECTION_LABELS = {
    "all": "Semua",
    "selected": "Dipilih",
    "unselected": "Belum dipilih",
}

# validasi / eksekusi change plan: label, tone, ikon
PLAN_STATUS_META = {
    "valid": ("Valid", "success", "✓"),
    "stale": ("Kedaluwarsa", "warning", "↻"),
    "conflict": ("Konflik", "warning", "!"),
    "unsupported": ("Tidak didukung", "muted", "–"),
    "rejected": ("Ditolak", "danger", "✕"),
    "applied": ("Diterapkan", "success", "✓"),
    "skipped": ("Dilewati", "muted", "–"),
    "failed": ("Gagal", "danger", "✕"),
    "not_applied": ("Belum diproses", "muted", "○"),
}

OPERATION_LABELS = {
    "replace_text": "Ganti teks",
    "apply_italic": "Terapkan italic",
}

_BADGE_STATE_META = {
    "not_run": ("Belum diperiksa", "muted", "○"),
    "done": ("Sudah diperiksa", "success", "✓"),
    "none_selected": ("Belum ada yang dipilih", "muted", "○"),
    "selected": ("dipilih", "accent", "●"),
    "repair_none": ("Belum ada perbaikan", "muted", "○"),
    "repair_ready": ("Perbaikan siap diunduh", "success", "✓"),
    "repair_blocked": ("Unduhan perbaikan diblokir", "danger", "✕"),
}


def severity_tone(severity: str) -> str:
    return SEVERITY_META.get(severity, ("neutral", "○", severity))[0]


def severity_color(severity: str) -> str:
    """Warna teks (hex) untuk severity; aman kontras di atas putih."""
    return _TONE_TEXT_COLOR[severity_tone(severity)]


def severity_label(severity: str) -> str:
    return SEVERITY_META.get(severity, ("neutral", "○", severity))[2]


def category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)


def confidence_label(confidence: float) -> str:
    """Contoh: 'Yakin · 0,92'. Band mengikuti DECISION-008."""
    band = confidence_band(confidence)
    text = CONFIDENCE_LABELS[band][0]
    return f"{text} · {confidence:.2f}".replace(".", ",")


def badge_text_for_state(state: str, count: Optional[int] = None) -> str:
    """Teks badge status. `count` opsional untuk konteks jumlah."""
    if state not in _BADGE_STATE_META:
        raise ValueError(f"State badge tidak dikenal: {state!r}")
    text = _BADGE_STATE_META[state][0]
    if state == "selected":
        return f"{count or 0} {text}"
    if state == "done" and count is not None:
        return f"{text} · {count} temuan"
    return text


def badge_tone_for_state(state: str) -> str:
    return _BADGE_STATE_META[state][1]


def badge_icon_for_state(state: str) -> str:
    return _BADGE_STATE_META[state][2]


def format_location(block_path: str, run_index: int,
                    char_start: int, char_end: int) -> str:
    """Contoh: 'body/p[3] run[0] 12–18'."""
    return f"{block_path} run[{run_index}] {char_start}–{char_end}"


def format_file_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    kb = num_bytes / 1024
    if kb < 1024:
        return f"{kb:.0f} KB" if kb >= 10 else f"{kb:.1f} KB"
    return f"{kb / 1024:.1f} MB"


def document_stats(parts: Mapping[str, Sequence[Any]]) -> dict:
    """Hitung paragraf, tabel, dan sel dari `snapshot.parts`.

    Paragraf dan sel dihitung seperti versi sebelumnya; tabel = tabel
    tingkat atas di body (`body/table[i]`).
    """
    body = parts.get("document", [])
    paragraphs = sum(
        1 for b in body
        if b.block_type in {"paragraph", "heading", "list_item"}
    )
    cells = {
        "/".join(b.block_path.split("/")[:5])
        for b in body if "/table[" in b.block_path
    }
    tables = {
        "/".join(b.block_path.split("/")[:2])
        for b in body if "/table[" in b.block_path
    }
    blocks = sum(len(v) for v in parts.values())
    complex_runs = sum(
        1 for v in parts.values() for b in v for r in b.runs
        if r.is_complex_run
    )
    return {
        "paragraphs": paragraphs,
        "tables": len(tables),
        "cells": len(cells),
        "blocks": blocks,
        "complex_runs": complex_runs,
    }


def status_bar_text(filename: str, size_bytes: int,
                    paragraphs: int, tables: int) -> str:
    return (
        f"{filename} • {format_file_size(size_bytes)} • "
        f"{paragraphs} paragraf • {tables} tabel"
    )


@dataclass(frozen=True)
class Badge:
    label: str
    text: str
    tone: str
    icon: str


def check_badges(state: Mapping[str, Any]) -> List[Badge]:
    """Badge row dari session_state (atau dict biasa)."""
    out: List[Badge] = []
    for label, key in (
        ("Bahasa", "findings"),
        ("Istilah asing", "foreign_findings"),
        ("Format", "fmt_findings"),
    ):
        items = state.get(key)
        s = "not_run" if items is None else "done"
        count = None if items is None else len(items)
        out.append(Badge(label, badge_text_for_state(s, count),
                         badge_tone_for_state(s), badge_icon_for_state(s)))

    sel = state.get("selection_state")
    n_sel = len(sel.selected_ids) if sel is not None else 0
    s = "selected" if n_sel else "none_selected"
    out.append(Badge("Pilihan", badge_text_for_state(s, n_sel),
                     badge_tone_for_state(s), badge_icon_for_state(s)))

    s = repair_state(state)
    out.append(Badge("Perbaikan", badge_text_for_state(s),
                     badge_tone_for_state(s), badge_icon_for_state(s)))
    return out


def repair_state(state: Mapping[str, Any]) -> str:
    if state.get("repair_output_bytes") is None:
        return "repair_none"
    report = state.get("repair_report")
    critical = state.get("repair_critical", False)
    if report is not None and report.ok and not critical:
        return "repair_ready"
    return "repair_blocked"


STAGES: Tuple[Tuple[str, str], ...] = (
    ("📋", "Ringkasan"),
    ("🔍", "Pemeriksaan"),
    ("📝", "Tinjauan"),
    ("🛠️", "Perbaikan"),
    ("📦", "Ekspor"),
)


def stage_progress(state: Mapping[str, Any],
                   file_ready: bool) -> List[Tuple[str, str, str]]:
    """Return [(label_stage, status, teks_status)] untuk checklist.

    status: 'done' | 'current' | 'todo'.
    """
    checks_done = any(
        state.get(k) is not None
        for k in ("findings", "foreign_findings", "fmt_findings")
    )
    sel = state.get("selection_state")
    has_sel = bool(sel is not None and sel.selected_ids)
    repaired = state.get("repair_output_bytes") is not None
    done = [file_ready, checks_done, has_sel, repaired, repaired]
    if not file_ready:
        # State lama milik file sebelumnya; jangan tampilkan sebagai selesai.
        done = [False] * len(STAGES)
    texts_done = ["Dokumen terbaca", "Pemeriksaan dijalankan",
                  "Temuan dipilih", "Perbaikan diterapkan", "Siap diunduh"]
    texts_todo = ["Unggah dokumen", "Jalankan pemeriksaan",
                  "Pilih temuan", "Terapkan perubahan", "Unduh hasil"]
    out = []
    current_marked = False
    for i, (icon, name) in enumerate(STAGES):
        if done[i]:
            status, text = "done", texts_done[i]
        elif not current_marked:
            status, text = "current", texts_todo[i]
            current_marked = True
        else:
            status, text = "todo", texts_todo[i]
        out.append((f"{icon} {name}", status, text))
    return out


def stepper_steps(state: Mapping[str, Any],
                  file_ready: bool) -> List[dict]:
    """Data stepper horizontal: nomor, nama, status, keterangan singkat."""
    progress = stage_progress(state, file_ready)
    subs = [text for _, _, text in progress]
    if file_ready:
        runs = [state.get(k) for k in
                ("findings", "foreign_findings", "fmt_findings")]
        done_runs = [r for r in runs if r is not None]
        if done_runs:
            total = sum(len(r) for r in done_runs)
            subs[1] = f"{len(done_runs)}/3 cek · {total} temuan"
        sel = state.get("selection_state")
        if sel is not None and sel.selected_ids:
            subs[2] = f"{len(sel.selected_ids)} dipilih"
        rs = repair_state(state)
        if rs == "repair_ready":
            subs[4] = "Siap diunduh"
        elif rs == "repair_blocked":
            subs[3], subs[4] = "Ada kegagalan", "Diblokir"
    return [
        {"number": i + 1, "name": name, "status": status, "sub": subs[i]}
        for i, ((_, name), (_, status, _)) in enumerate(zip(STAGES, progress))
    ]


def stepper_html(steps: Sequence[Mapping[str, Any]]) -> str:
    items = []
    for s in steps:
        status = s["status"]
        dot = "✓" if status == "done" else str(s["number"])
        state_text = {"done": "selesai", "current": "tahap berikutnya",
                      "todo": "belum"}[status]
        aria = ' aria-current="step"' if status == "current" else ""
        items.append(
            f'<li class="dl-{status}"{aria}>'
            f'<span class="dl-step-dot" aria-hidden="true">{dot}</span>'
            f'<span class="dl-step-name">{escape(s["name"])}'
            f'<span class="sr-only"> ({state_text})</span></span>'
            f'<span class="dl-step-sub">{escape(s["sub"])}</span></li>'
        )
    return (
        '<ol class="dl-stepper" aria-label="Tahapan pemeriksaan">'
        + "".join(items) + "</ol>"
    )


LOGO_SVG = (
    '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" '
    'stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
    '<path d="M14 3v5h5"/><path d="m9 14 2 2 4-4"/></svg>'
)

_ICON_PATHS = {
    "shield": '<path d="M12 3 5 6v6c0 4 3 7.5 7 9 4-1.5 7-5 7-9V6z"/>'
              '<path d="m9 12 2 2 4-4"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
    "wand": '<path d="m4 20 11-11"/><path d="m14 4 1 2 2 1-2 1-1 2-1-2-2-1 '
            '2-1z"/><path d="M19 13v3M17.5 14.5h3"/>',
    "download": '<path d="M12 4v11"/><path d="m7 11 5 5 5-5"/>'
                '<path d="M5 20h14"/>',
}


def icon_svg(name: str, size: int = 20) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{_ICON_PATHS[name]}</svg>'
    )


def hero_html(public_demo: bool) -> str:
    if public_demo:
        mode_badge = pill_html("Demo publik · dokumen non-sensitif",
                               "warning", "!")
    else:
        mode_badge = pill_html("Diproses lokal", "success", "✓")
    badges = mode_badge + pill_html("Tanpa AI generatif", "accent", "●")
    return (
        '<header class="dl-hero">'
        f'<div class="dl-logo">{LOGO_SVG}</div>'
        '<div class="dl-hero-text">'
        '<div class="dl-hero-title">Docx<span class="dl-grad">Lint</span></div>'
        '<div class="dl-hero-sub">Periksa ejaan, istilah asing, dan format '
        "dokumen Word, lalu perbaiki salinannya dengan aman.</div></div>"
        f'<div class="dl-hero-badges">{badges}</div>'
        "</header>"
    )


LANDING_FEATURES = (
    ("shield", "Validasi aman",
     "ZIP, makro, dan path traversal dicek sebelum dokumen dibaca."),
    ("search", "Periksa bahasa dan istilah",
     "Ejaan, kata tidak dikenal, istilah asing, italic, dan format."),
    ("wand", "Perbaiki dengan persetujuan",
     "Hanya temuan yang Anda pilih dan konfirmasi yang diterapkan."),
    ("download", "Unduh salinan",
     "Dokumen asli tidak pernah ditimpa; hasil divalidasi ulang."),
)


def landing_html() -> str:
    cards = "".join(
        '<div class="dl-feature">'
        f'<div class="dl-feature-ico">{icon_svg(icon)}</div>'
        f'<div class="dl-feature-title">{escape(title)}</div>'
        f'<div class="dl-feature-body">{escape(body)}</div></div>'
        for icon, title, body in LANDING_FEATURES
    )
    steps = " → ".join(
        f"<b>{i}</b>&nbsp;{escape(name)}"
        for i, (_, name) in enumerate(STAGES, start=1)
    )
    return (
        f'<div class="dl-landing">{cards}</div>'
        f'<div class="dl-steps-inline">Alur: {steps}</div>'
    )


def footer_html(version: str) -> str:
    return (
        f'<div class="dl-footer">DocxLint v{escape(version)} · '
        "Konten dokumen diproses di memori dan tidak dikirim ke layanan "
        "eksternal.</div>"
    )


def file_status(file_ready: bool, analyzed: bool) -> List[Badge]:
    """Badge status file: uploaded / validated / analyzed."""
    def b(label: str, ok: bool) -> Badge:
        return Badge(label, "Ya" if ok else "Belum",
                     "success" if ok else "muted", "✓" if ok else "○")
    return [
        b("Diunggah", True),
        b("Tervalidasi", file_ready),
        b("Dianalisis", analyzed),
    ]


def pill_html(text: str, tone: str = "neutral", icon: str = "") -> str:
    ico = f'<span class="dl-ico" aria-hidden="true">{escape(icon)}</span>' \
        if icon else ""
    return (
        f'<span class="dl-pill dl-tone-{escape(tone)}">'
        f"{ico}{escape(str(text))}</span>"
    )


def finding_header_html(f: Any, occurrences: int = 1) -> str:
    """HTML kepala card temuan (pill + nilai + saran + alasan + lokasi).

    `occurrences` > 1 dipakai card kelompok: lokasi diringkas menjadi
    jumlah lokasi plus lokasi pertama.
    """
    band = confidence_band(f.confidence)
    conf_text, conf_tone, conf_icon = CONFIDENCE_LABELS[band]
    sev_tone, sev_icon, sev_text = SEVERITY_META.get(
        f.severity, ("neutral", "○", f.severity)
    )
    pill_list = [
        pill_html(category_label(f.category), "neutral"),
        pill_html(f"Severity: {sev_text}", sev_tone, sev_icon),
        pill_html(f"Confidence: {confidence_label(f.confidence)}",
                  conf_tone, conf_icon),
    ]
    if occurrences > 1:
        pill_list.append(pill_html(f"{occurrences} lokasi", "accent", "×"))
    pills = "".join(pill_list)
    title = f'<span class="dl-card-title">{escape(f.original_value or "")}</span>'
    if f.suggested_value:
        title += (
            '<span class="dl-card-arrow" aria-label="menjadi">→</span>'
            f'<span class="dl-card-suggest">{escape(f.suggested_value)}</span>'
        )
    loc = f.location
    location = format_location(loc.block_path, loc.run_index,
                               loc.char_start, loc.char_end)
    loc_label = (
        f"Lokasi pertama dari {occurrences}: " if occurrences > 1
        else "Lokasi: "
    )
    return (
        f'<div class="dl-row">{pills}</div>'
        f"<div>{title}</div>"
        f'<div class="dl-muted">{escape(f.reason or "")}</div>'
        f'<div class="dl-mono">{loc_label}{escape(location)}</div>'
    )


def change_plan_table_html(items: Iterable[Any],
                           use_execution: bool = False) -> str:
    rows = []
    for item in items:
        status = item.execution if use_execution else item.validation
        label, tone, icon = PLAN_STATUS_META.get(
            status, (status, "neutral", "")
        )
        if item.is_text_edit():
            detail = (
                f"<strong>{escape(item.original_value or '')}</strong> → "
                f"{escape(item.replacement or '')}"
            )
        else:
            detail = f"<em>{escape(item.original_value or '')}</em>"
        loc = format_location(item.block_path, item.run_index,
                              item.char_start, item.char_end)
        rows.append(
            "<tr>"
            f"<td>{pill_html(label, tone, icon)}</td>"
            f"<td>{escape(OPERATION_LABELS.get(item.operation, item.operation))}</td>"
            f"<td>{detail}</td>"
            f'<td class="dl-mono">{escape(loc)}</td>'
            f"<td>{escape(item.reason or '—')}</td>"
            "</tr>"
        )
    return (
        '<div class="dl-table-wrap"><table class="dl-table">'
        "<thead><tr><th>Status</th><th>Operasi</th>"
        "<th>Original → Pengganti</th><th>Lokasi</th><th>Alasan</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    )


# ---------------------------------------------------------------------------
# Render (Streamlit)
# ---------------------------------------------------------------------------

def _st():
    import streamlit as st
    return st


def render_status_bar(filename: str, size_bytes: int,
                      paragraphs: int, tables: int) -> None:
    sep = '<span class="dl-sep" aria-hidden="true">•</span>'
    parts = [
        f'<span aria-hidden="true">📄</span>'
        f'<span class="dl-file">{escape(filename)}</span>',
        escape(format_file_size(size_bytes)),
        f"{paragraphs} paragraf",
        f"{tables} tabel",
    ]
    _st().markdown(
        f'<div class="dl-statusbar" role="status" '
        f'aria-label="{escape(status_bar_text(filename, size_bytes, paragraphs, tables))}">'
        + sep.join(parts) + "</div>",
        unsafe_allow_html=True,
    )


def render_hero(public_demo: bool) -> None:
    _st().markdown(hero_html(public_demo), unsafe_allow_html=True)


def render_stepper(steps: Sequence[Mapping[str, Any]]) -> None:
    _st().markdown(stepper_html(steps), unsafe_allow_html=True)


def render_landing() -> None:
    _st().markdown(landing_html(), unsafe_allow_html=True)


def render_footer(version: str) -> None:
    _st().markdown(footer_html(version), unsafe_allow_html=True)


def render_badges(badges: Iterable[Badge]) -> None:
    html = "".join(
        pill_html(f"{b.label}: {b.text}", b.tone, b.icon) for b in badges
    )
    _st().markdown(f'<div class="dl-row">{html}</div>',
                   unsafe_allow_html=True)


def render_metric_row(metrics: Sequence[Tuple[str, Any]],
                      helps: Optional[Sequence[Optional[str]]] = None) -> None:
    st = _st()
    cols = st.columns(len(metrics))
    for i, (col, (label, value)) in enumerate(zip(cols, metrics)):
        h = helps[i] if helps else None
        col.metric(label, value, help=h, border=True)


def render_finding_card(f: Any, occurrences: int = 1) -> None:
    """Kepala card; dipanggil di dalam container ber-border."""
    _st().markdown(finding_header_html(f, occurrences),
                   unsafe_allow_html=True)


def render_empty_state(title: str, body: str = "") -> None:
    _st().markdown(
        f'<div class="dl-empty"><div class="dl-empty-title">'
        f"{escape(title)}</div><div>{escape(body)}</div></div>",
        unsafe_allow_html=True,
    )


def _banner(title: str, body: str, tone: str, icon: str,
            role: str = "status") -> None:
    _st().markdown(
        f'<div class="dl-banner dl-tone-{tone}" role="{role}">'
        f'<div class="dl-banner-title"><span aria-hidden="true">{icon}</span> '
        f"{escape(title)}</div><div>{escape(body)}</div></div>",
        unsafe_allow_html=True,
    )


def render_error_banner(title: str, body: str = "") -> None:
    """Banner error tanpa traceback dan tanpa isi dokumen."""
    _banner(title, body, "danger", "✕", role="alert")


def render_warning_banner(title: str, body: str = "") -> None:
    _banner(title, body, "warning", "!")


def render_success_banner(title: str, body: str = "") -> None:
    _banner(title, body, "success", "✓")


def render_meta_card(rows: Sequence[Tuple[str, Any]]) -> None:
    items = "".join(
        f"<dt>{escape(str(k))}</dt><dd>{escape(str(v))}</dd>"
        for k, v in rows
    )
    st = _st()
    with st.container(border=True):
        st.markdown(f'<dl class="dl-meta">{items}</dl>',
                    unsafe_allow_html=True)


__all__ = [
    "Badge", "STAGES",
    "severity_color", "severity_tone", "severity_label", "category_label",
    "confidence_label", "badge_text_for_state", "badge_tone_for_state",
    "format_location", "format_file_size", "document_stats",
    "status_bar_text", "check_badges", "repair_state", "stage_progress",
    "file_status", "pill_html", "finding_header_html",
    "change_plan_table_html",
    "render_status_bar", "render_badges", "render_metric_row",
    "render_finding_card", "render_empty_state", "render_error_banner",
    "render_warning_banner", "render_success_banner", "render_meta_card",
    "stepper_steps", "stepper_html", "hero_html", "landing_html",
    "footer_html", "icon_svg", "LOGO_SVG", "render_hero",
    "render_stepper", "render_landing", "render_footer",
]
