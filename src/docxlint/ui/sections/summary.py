"""Stage 1 — Ringkasan: metadata, struktur, dan konfigurasi aktif."""

import streamlit as st

from ...config import DEFAULT_FOREIGN_POLICY
from ..components import (
    format_file_size,
    pill_html,
    render_meta_card,
)

MAX_PREVIEW_BLOCKS = 200


def render_summary_section(filename, size_bytes, snapshot, stats,
                           dictionary, glossary, active_profile) -> None:
    left, right = st.columns([0.55, 0.45])

    with left:
        st.subheader("Dokumen")
        render_meta_card([
            ("Nama file", filename),
            ("Ukuran", format_file_size(size_bytes)),
            ("Paragraf", stats["paragraphs"]),
            ("Tabel", stats["tables"]),
            ("Sel tabel", stats["cells"]),
            ("Total blok", stats["blocks"]),
            ("Run kompleks", stats["complex_runs"]),
            ("Bagian", ", ".join(snapshot.parts.keys())),
        ])

    with right:
        st.subheader("Konfigurasi")
        d = dictionary.status
        g = glossary.status
        rows = [
            ("Kamus", f"{d.word_count} kata" if d.loaded else "Belum siap"),
            ("Whitelist", d.whitelist_count if d.loaded else "—"),
            ("Glossary", f"{g.entry_count} entri" if g.loaded else "Belum siap"),
        ]
        if active_profile is not None:
            rows.append(("Profil", f"{active_profile.name} "
                                   f"(v{active_profile.version})"))
            rows.append(("Aturan format",
                         len(active_profile.enabled_rules())))
        else:
            rows.append(("Profil", "Tidak ada"))
        render_meta_card(rows)

        if active_profile is not None:
            with st.expander("Aturan profil aktif"):
                for rule in active_profile.enabled_rules():
                    st.markdown(
                        f"- `{rule.rule_id}` (severity={rule.severity}) "
                        f"— params: {rule.params}"
                    )
        with st.expander("Kebijakan istilah asing"):
            st.write(
                {
                    "review_configured_foreign_terms":
                        DEFAULT_FOREIGN_POLICY.review_configured_foreign_terms,
                    "review_unlisted_foreign_candidates":
                        DEFAULT_FOREIGN_POLICY.review_unlisted_foreign_candidates,
                    "ignore_acronyms": DEFAULT_FOREIGN_POLICY.ignore_acronyms,
                    "respect_existing_italic":
                        DEFAULT_FOREIGN_POLICY.respect_existing_italic,
                    "case_sensitive_terms":
                        DEFAULT_FOREIGN_POLICY.case_sensitive_terms,
                }
            )

    st.subheader("Struktur dokumen")
    for part_name, blocks in snapshot.parts.items():
        if not blocks:
            continue
        with st.expander(f"Bagian {part_name} — {len(blocks)} blok",
                         expanded=part_name == "document"):
            for block in blocks[:MAX_PREVIEW_BLOCKS]:
                complex_count = sum(1 for r in block.runs if r.is_complex_run)
                marker = (
                    pill_html(f"{complex_count} run kompleks", "warning", "!")
                    if complex_count else ""
                )
                preview = block.text[:120].replace("\n", " ")
                st.markdown(
                    f'<div class="dl-mono">{block.block_path} '
                    f"[{block.block_type}] {marker}</div>",
                    unsafe_allow_html=True,
                )
                st.text(preview or "(kosong)")
            if len(blocks) > MAX_PREVIEW_BLOCKS:
                st.caption(
                    f"… {len(blocks) - MAX_PREVIEW_BLOCKS} blok lainnya "
                    "tidak ditampilkan."
                )
