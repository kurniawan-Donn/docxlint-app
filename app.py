"""DocxLint — UI Streamlit (Phase 7.5).

Orchestrator tipis: tema → upload → validasi/baca → stage tabs.
Tampilan per stage ada di `src/docxlint/ui/sections/`.

Alur: upload → validate → read → analyze → preview → review → repair →
download. Semua pemrosesan dokumen berjalan di dalam `network_guard()`.
"""

import hashlib
import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.docxlint.config import (  # noqa: E402
    CONFIG_DIR_NAME,
    EXCEPTIONS_FILE,
    PROFILES_DIR_NAME,
    TERMINOLOGY_FILE,
)
from src.docxlint.services.config_service import (  # noqa: E402
    compute_config_hash,
)
from src.docxlint.services.dictionary_service import (  # noqa: E402
    DictionaryService,
)
from src.docxlint.services.docx_reader import read_document  # noqa: E402
from src.docxlint.services.docx_validator import DocxValidator  # noqa: E402
from src.docxlint.services.glossary_service import (  # noqa: E402
    GlossaryService,
)
from src.docxlint.services.invalidation import (  # noqa: E402
    mark_stale_findings,
)
from src.docxlint.services.network_guard import network_guard  # noqa: E402
from src.docxlint.services.profile_service import (  # noqa: E402
    ProfileRegistry,
)
from src.docxlint.ui.components import (  # noqa: E402
    STAGES,
    check_badges,
    document_stats,
    file_status,
    pill_html,
    render_badges,
    render_empty_state,
    render_error_banner,
    render_status_bar,
    stage_progress,
)
from src.docxlint.ui.sections.checks import render_checks_section  # noqa: E402
from src.docxlint.ui.sections.export import render_export_section  # noqa: E402
from src.docxlint.ui.sections.repair import render_repair_section  # noqa: E402
from src.docxlint.ui.sections.review import render_review_section  # noqa: E402
from src.docxlint.ui.sections.summary import (  # noqa: E402
    render_summary_section,
)
from src.docxlint.ui.theme import inject_theme  # noqa: E402
from src.docxlint.utils.errors import ValidationError  # noqa: E402


st.set_page_config(page_title="DocxLint", page_icon="📄", layout="wide")
inject_theme()


@st.cache_resource(show_spinner=False)
def _load_dictionary(config_dir: str):
    svc = DictionaryService(Path(config_dir))
    svc.load()
    return svc


@st.cache_resource(show_spinner=False)
def _load_glossary(config_dir: str):
    cfg = Path(config_dir)
    svc = GlossaryService(cfg / TERMINOLOGY_FILE, cfg / EXCEPTIONS_FILE)
    svc.load()
    return svc


@st.cache_resource(show_spinner=False)
def _load_profiles(profiles_dir: str):
    reg = ProfileRegistry(Path(profiles_dir))
    reg.load()
    return reg


def _dedupe_findings(findings):
    seen = set()
    out = []
    for f in findings:
        if f.finding_id in seen:
            continue
        seen.add(f.finding_id)
        out.append(f)
    return out


def _read_snapshot(data: bytes):
    """Baca snapshot sekali per file.

    `read_document` membuat snapshot_id baru tiap panggilan; tanpa cache,
    setiap rerun mereset `SelectionState` sehingga pilihan hilang.
    """
    digest = hashlib.sha256(data).hexdigest()
    cached = st.session_state.get("_snapshot_cache")
    if cached is not None and cached[0] == digest:
        return cached[1]
    snapshot = read_document(data)
    st.session_state["_snapshot_cache"] = (digest, snapshot)
    return snapshot


def _render_sidebar_status(file_box, steps_box, filename, size_label,
                           file_ready: bool) -> None:
    analyzed = file_ready and any(
        st.session_state.get(k) is not None
        for k in ("findings", "foreign_findings", "fmt_findings")
    )
    with file_box:
        st.markdown("**Status file**")
        if filename is None:
            st.caption("Belum ada file diunggah.")
        else:
            st.markdown(f"`{filename}`  \n{size_label}")
            html = "".join(
                pill_html(f"{b.label}: {b.text}", b.tone, b.icon)
                for b in file_status(file_ready, analyzed)
            )
            st.markdown(f'<div class="dl-row">{html}</div>',
                        unsafe_allow_html=True)
    with steps_box:
        st.markdown("**Tahapan**")
        icons = {"done": "✓", "current": "→", "todo": "○"}
        texts = {"done": "Selesai", "current": "Berikutnya", "todo": "Nanti"}
        items = "".join(
            f'<li><span aria-hidden="true">{icons[s]}</span>'
            f"<span>{label}<br><span class=\"dl-step-state\">"
            f"{texts[s]} · {t}</span></span></li>"
            for label, s, t in stage_progress(st.session_state, file_ready)
        )
        st.markdown(f'<ul class="dl-steps">{items}</ul>',
                    unsafe_allow_html=True)
        st.caption("Buka tahap lewat tab di area utama.")


# --- Sidebar --------------------------------------------------------------
with st.sidebar:
    st.title("DocxLint")
    st.caption("Pemeriksa DOCX lokal. Tanpa AI, tanpa jaringan.")
    sidebar_file_box = st.container()
    sidebar_steps_box = st.container()
    st.divider()

    profiles_dir = _ROOT / CONFIG_DIR_NAME / PROFILES_DIR_NAME
    registry = _load_profiles(str(profiles_dir))
    profiles = registry.list()
    active_profile = None

    st.markdown("**Profil formatting**")
    if not profiles:
        render_error_banner(
            "Tidak ada profil",
            f"Letakkan file YAML di config/{PROFILES_DIR_NAME}/.",
        )
    else:
        profile_labels = {p.profile_id: p.name for p in profiles}
        default_id = st.session_state.get("active_profile_id")
        if default_id not in profile_labels:
            default_id = profiles[0].profile_id
        selected_id = st.selectbox(
            "Profil formatting aktif",
            options=list(profile_labels.keys()),
            format_func=lambda x: profile_labels[x],
            index=list(profile_labels.keys()).index(default_id),
            key="profile_select",
            help="Mengganti profil membuat temuan dan rencana perubahan "
                 "lama kedaluwarsa.",
        )
        active_profile = registry.get(selected_id)
        if active_profile is None:
            render_error_banner("Profil tidak dapat dimuat", "")
        else:
            st.session_state["active_profile_id"] = active_profile.profile_id
            st.session_state["active_profile_version"] = active_profile.version
            st.markdown(
                pill_html(f"Versi {active_profile.version}", "accent")
                + " "
                + pill_html(f"Skema {active_profile.schema_version}",
                            "neutral"),
                unsafe_allow_html=True,
            )
            if active_profile.description:
                st.caption(active_profile.description)

    st.divider()
    st.caption(
        "Mode lokal: konten dokumen tidak dikirim ke layanan eksternal."
    )

# --- Header & upload -------------------------------------------------------
status_slot = st.container()
badge_slot = st.container()

uploaded = st.file_uploader(
    "Unggah file .docx",
    type=["docx"],
    help="Satu dokumen per sesi. File diproses di memori secara lokal.",
)

if uploaded is None:
    with status_slot:
        st.title("DocxLint")
    render_empty_state(
        "Belum ada dokumen",
        "Unggah file .docx untuk mulai: validasi, pemeriksaan, tinjauan, "
        "perbaikan, lalu unduh salinan.",
    )
    _render_sidebar_status(sidebar_file_box, sidebar_steps_box,
                           None, "", False)
    st.stop()

data = uploaded.getvalue()
filename = uploaded.name
validator = DocxValidator()

try:
    with network_guard():
        validator.validate(data, filename)
        snapshot = _read_snapshot(data)
except ValidationError as exc:
    render_error_banner("Validasi gagal", str(exc))
    _render_sidebar_status(sidebar_file_box, sidebar_steps_box,
                           filename, f"{len(data) / 1024:.1f} KB", False)
    st.stop()
except Exception:
    render_error_banner(
        "Dokumen tidak dapat diproses",
        "Terjadi kesalahan saat membaca dokumen. Pastikan file adalah "
        "DOCX yang valid lalu coba lagi.",
    )
    _render_sidebar_status(sidebar_file_box, sidebar_steps_box,
                           filename, f"{len(data) / 1024:.1f} KB", False)
    st.stop()

stats = document_stats(snapshot.parts)

config_dir = _ROOT / CONFIG_DIR_NAME
dictionary = _load_dictionary(str(config_dir))
glossary = _load_glossary(str(config_dir))

# --- Stage tabs ------------------------------------------------------------
tabs = st.tabs([f"{icon} {name}" for icon, name in STAGES])

with tabs[0]:
    render_summary_section(filename, len(data), snapshot, stats,
                           dictionary, glossary, active_profile)

with tabs[1]:
    render_checks_section(snapshot, dictionary, glossary, active_profile)

combined = []
combined.extend(st.session_state.get("findings") or [])
combined.extend(st.session_state.get("foreign_findings") or [])
combined = _dedupe_findings(combined)

with tabs[2]:
    if not combined:
        st.subheader("Tinjau Temuan")
        render_empty_state(
            "Belum ada temuan",
            "Jalankan pemeriksaan bahasa atau istilah asing di tab "
            "Pemeriksaan terlebih dahulu.",
        )
    else:
        with network_guard():
            render_review_section(combined, snapshot)

if combined:
    # --- Phase 7: invalidasi berdasarkan profil aktif ---
    current_profile_id = st.session_state.get("active_profile_id", "")
    current_config_hash = ""
    if active_profile is not None:
        current_config_hash = compute_config_hash(active_profile.to_dict())

    combined = mark_stale_findings(
        combined, current_profile_id, current_config_hash,
    )

    st.session_state["current_profile_id"] = current_profile_id
    st.session_state["current_config_hash"] = current_config_hash

with tabs[3]:
    if not combined:
        st.subheader("Rencana Perubahan & Perbaikan")
        render_empty_state(
            "Belum ada temuan",
            "Perbaikan membutuhkan temuan yang sudah dipilih di tab "
            "Tinjauan.",
        )
    else:
        with network_guard():
            render_repair_section(combined, snapshot, data, filename)

with tabs[4]:
    render_export_section(data, filename)

# --- Status bar, badge, sidebar (diisi terakhir agar mencerminkan state
# setelah tombol pada rerun ini diproses) -----------------------------------
with status_slot:
    render_status_bar(filename, len(data), stats["paragraphs"],
                      stats["tables"])
with badge_slot:
    render_badges(check_badges(st.session_state))
_render_sidebar_status(sidebar_file_box, sidebar_steps_box, filename,
                       f"{len(data) / 1024:.1f} KB", True)
