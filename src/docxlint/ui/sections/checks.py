"""Stage 2 — Pemeriksaan (bahasa, istilah asing, format).

Logika tombol dipindah apa adanya dari `app.py` (Phase 3/4/7).
Setiap checker tetap dijalankan di dalam `network_guard()`.
"""

from dataclasses import replace

import streamlit as st

from ...config import DEFAULT_FOREIGN_POLICY
from ...models.finding import CATEGORY_ITALIC_FORMATTING
from ...services.config_service import compute_config_hash
from ...services.foreign_terms_checker import ForeignTermsChecker
from ...services.formatting_checker import FormattingChecker
from ...services.language_checker import LanguageChecker
from ...services.network_guard import network_guard
from ..components import (
    render_empty_state,
    render_finding_card,
    render_metric_row,
    render_success_banner,
    render_warning_banner,
)

MAX_FMT_VISIBLE = 200


def render_checks_section(snapshot, dictionary, glossary,
                          active_profile) -> None:
    st.subheader("Pemeriksaan")
    st.caption(
        "Pemeriksaan hanya mendeteksi. Dokumen tidak diubah. Hasil "
        "bergantung pada cakupan kamus dan glossary lokal."
    )
    _render_language(snapshot, dictionary)
    _render_foreign(snapshot, dictionary, glossary)
    _render_formatting(snapshot, active_profile)


def _render_language(snapshot, dictionary) -> None:
    with st.container(border=True):
        st.markdown("#### Bahasa")
        status = dictionary.status
        if not status.loaded:
            render_warning_banner(
                "Kamus belum siap",
                f"{status.error or 'Tidak diketahui'}. Sediakan "
                "config/dictionary_id.txt (satu kata per baris).",
            )
            return

        st.caption(
            f"Kamus: {status.word_count} kata · whitelist "
            f"{status.whitelist_count} · pengecualian "
            f"{status.exception_count} · istilah "
            f"{status.terminology_count}. Sumber: kurasi manual "
            "(DECISION-018)."
        )

        if st.button("Jalankan pemeriksaan bahasa", type="primary",
                     key="btn_check_language"):
            with st.spinner("Memeriksa ejaan…"):
                with network_guard():
                    checker = LanguageChecker(dictionary)
                    findings = checker.check(snapshot)
            st.session_state["findings"] = findings
            st.session_state["tokens_scanned"] = checker.tokens_scanned
            st.session_state["skipped_runs"] = checker.skipped_complex_runs

        findings = st.session_state.get("findings")
        if findings is None:
            st.caption("Belum diperiksa.")
            return

        tokens_scanned = st.session_state.get("tokens_scanned", 0)
        skipped_runs = st.session_state.get("skipped_runs", 0)
        spelling = [f for f in findings if f.category == "spelling"]
        unknown = [f for f in findings if f.category == "unknown_word"]

        render_metric_row([
            ("Token diperiksa", tokens_scanned),
            ("Total temuan", len(findings)),
            ("Kemungkinan salah eja", len(spelling)),
            ("Kata tidak dikenal", len(unknown)),
        ])
        if skipped_runs:
            st.caption(
                f"{skipped_runs} run kompleks dilewati "
                "(DECISION-021: tidak diforsir)."
            )
        if not findings:
            render_success_banner("Tidak ada temuan bahasa", "")
        else:
            st.caption("Pilih dan tandai temuan di tab **Tinjauan**.")


def _render_foreign(snapshot, dictionary, glossary) -> None:
    with st.container(border=True):
        st.markdown("#### Istilah asing dan italic")
        if not glossary.status.loaded or glossary.status.entry_count == 0:
            render_warning_banner(
                "Glossary belum siap",
                "Sediakan config/terminology.csv dengan kolom: term, "
                "italic, category, note.",
            )
            return

        st.caption(
            f"Glossary: {glossary.status.entry_count} entri · "
            f"pengecualian {glossary.status.exception_count}. Italic hanya "
            "direkomendasikan untuk istilah terdaftar (DECISION-009)."
        )

        review_unlisted = st.checkbox(
            "Deteksi kandidat istilah asing tak terdaftar (belum pasti)",
            value=DEFAULT_FOREIGN_POLICY.review_unlisted_foreign_candidates,
            help="Kandidat ditandai uncertain; bukan kepastian typo/asing.",
            key="chk_review_unlisted",
        )

        if st.button("Jalankan pemeriksaan istilah asing", type="primary",
                     key="btn_check_foreign"):
            policy = DEFAULT_FOREIGN_POLICY
            if review_unlisted != policy.review_unlisted_foreign_candidates:
                policy = replace(
                    policy,
                    review_unlisted_foreign_candidates=review_unlisted,
                )
            with st.spinner("Memeriksa istilah asing…"):
                with network_guard():
                    checker = ForeignTermsChecker(
                        glossary=glossary,
                        dictionary=dictionary,
                        policy=policy,
                    )
                    foreign_findings = checker.check(snapshot)
            st.session_state["foreign_findings"] = foreign_findings
            st.session_state["foreign_matches"] = checker.matches_seen

        foreign_findings = st.session_state.get("foreign_findings")
        if foreign_findings is None:
            st.caption("Belum diperiksa.")
            return

        configured = [
            f for f in foreign_findings
            if f.metadata.get("match_type") == "configured"
        ]
        candidates = [
            f for f in foreign_findings
            if f.metadata.get("match_type") == "candidate"
        ]
        italic_issues = [
            f for f in foreign_findings
            if f.category == CATEGORY_ITALIC_FORMATTING
        ]
        uncertain = [
            f for f in foreign_findings
            if f.metadata.get("uncertain") is True
        ]
        render_metric_row([
            ("Cocok glossary", len(configured)),
            ("Kandidat asing", len(candidates)),
            ("Isu italic", len(italic_issues)),
            ("Belum pasti", len(uncertain)),
        ])
        if not foreign_findings:
            render_success_banner("Tidak ada temuan istilah asing", "")
        else:
            st.caption("Pilih dan tandai temuan di tab **Tinjauan**.")


def _render_formatting(snapshot, active_profile) -> None:
    with st.container(border=True):
        st.markdown("#### Format")
        if active_profile is None:
            render_warning_banner(
                "Profil formatting belum tersedia",
                "Pilih profil di sidebar atau letakkan file YAML di "
                "config/profiles/.",
            )
            return

        st.caption(
            f"Profil aktif: {active_profile.name} "
            f"(v{active_profile.version}) · "
            f"{len(active_profile.enabled_rules())} aturan aktif. "
            "Temuan format hanya ditampilkan (belum masuk Tinjauan)."
        )

        if st.button("Jalankan pemeriksaan format", type="primary",
                     key="btn_check_format"):
            checker = FormattingChecker(active_profile)
            with st.spinner("Memeriksa format…"):
                with network_guard():
                    fmt_findings = checker.check(snapshot)
            st.session_state["fmt_findings"] = fmt_findings
            st.session_state["fmt_profile_id"] = active_profile.profile_id
            st.session_state["fmt_profile_version"] = active_profile.version
            st.session_state["fmt_config_hash"] = compute_config_hash(
                active_profile.to_dict()
            )

        fmt_findings = st.session_state.get("fmt_findings")
        if fmt_findings is None:
            st.caption("Belum diperiksa.")
            return
        if not fmt_findings:
            render_success_banner("Tidak ada temuan format", "")
            return

        st.caption(f"Temuan format: {len(fmt_findings)}")
        with st.expander("Lihat temuan format", expanded=False):
            for f in fmt_findings[:MAX_FMT_VISIBLE]:
                with st.container(border=True):
                    render_finding_card(f)
            if len(fmt_findings) > MAX_FMT_VISIBLE:
                render_empty_state(
                    f"{len(fmt_findings) - MAX_FMT_VISIBLE} temuan lain "
                    "tidak ditampilkan",
                    "",
                )
