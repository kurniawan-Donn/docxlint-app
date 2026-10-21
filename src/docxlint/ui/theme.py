"""Design tokens dan injeksi CSS (Phase 7.5).

Token dan helper kontras bersifat murni (tanpa Streamlit) agar dapat
ditest. Hanya `inject_theme()` yang menyentuh Streamlit.

Dua palet: terang (`LIGHT`, juga diekspor sebagai `COLORS`) dan gelap
(`DARK`). Semua aturan CSS memakai variabel `--dl-*`, sehingga mengganti
mode cukup mengganti blok variabel.
"""

from typing import Dict, Optional, Tuple

# --- Warna -----------------------------------------------------------------
# `*_text` adalah varian untuk teks agar kontras >= 4.5:1 (WCAG AA) di atas
# surface dan latar soft-nya. Warna dasar dipakai untuk border/aksen.
LIGHT: Dict[str, str] = {
    "bg": "#F7F8FB",
    "surface": "#FFFFFF",
    "border": "#E3E7EE",
    "text": "#111827",
    "secondary": "#5B6472",
    "muted_text": "#4B5563",
    "accent": "#2563EB",
    "accent_soft": "#EFF6FF",
    "violet": "#7C3AED",
    "violet_soft": "#F5F3FF",
    "on_accent": "#FFFFFF",
    "success": "#059669",
    "success_text": "#047857",
    "success_soft": "#ECFDF5",
    "warning": "#D97706",
    "warning_text": "#B45309",
    "warning_soft": "#FFFBEB",
    "danger": "#DC2626",
    "danger_text": "#B91C1C",
    "danger_soft": "#FEF2F2",
    "neutral_soft": "#F1F3F7",
    "shadow": "rgba(17, 24, 39, 0.08)",
}

DARK: Dict[str, str] = {
    "bg": "#0D1117",
    "surface": "#161B22",
    "border": "#2D333B",
    "text": "#E6EDF3",
    "secondary": "#9DA7B3",
    "muted_text": "#B1BAC4",
    "accent": "#60A5FA",
    "accent_soft": "#132447",
    "violet": "#A78BFA",
    "violet_soft": "#221641",
    "on_accent": "#FFFFFF",
    "success": "#10B981",
    "success_text": "#34D399",
    "success_soft": "#0B2A22",
    "warning": "#F59E0B",
    "warning_text": "#FBBF24",
    "warning_soft": "#2B1D06",
    "danger": "#EF4444",
    "danger_text": "#F87171",
    "danger_soft": "#2E1215",
    "neutral_soft": "#21262D",
    "shadow": "rgba(0, 0, 0, 0.45)",
}

# Kompatibilitas: kode lama memakai COLORS sebagai palet terang.
COLORS = LIGHT
PALETTES: Dict[str, Dict[str, str]] = {"light": LIGHT, "dark": DARK}

SPACING: Tuple[int, ...] = (4, 8, 12, 16, 24, 32)
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 16
FONT_STACK = (
    'system-ui, -apple-system, "Segoe UI Variable Text", "Segoe UI", '
    'Roboto, "Helvetica Neue", Arial, sans-serif'
)
FONT_MONO = (
    'ui-monospace, SFMono-Regular, "Cascadia Mono", Consolas, '
    '"Liberation Mono", monospace'
)
FONT_SIZE_BASE = 14
FONT_SIZE_HEADING = (20, 26)

# Pasangan (teks, latar) yang benar-benar dipakai UI untuk teks; diuji
# untuk kedua palet.
TEXT_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("text", "surface"),
    ("text", "bg"),
    ("secondary", "surface"),
    ("secondary", "bg"),
    ("accent", "surface"),
    ("accent", "accent_soft"),
    ("text", "accent_soft"),
    ("text", "violet_soft"),
    ("secondary", "accent_soft"),
    ("success_text", "surface"),
    ("success_text", "success_soft"),
    ("warning_text", "surface"),
    ("warning_text", "warning_soft"),
    ("danger_text", "surface"),
    ("danger_text", "danger_soft"),
    ("text", "neutral_soft"),
    ("muted_text", "neutral_soft"),
)


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    v = value.lstrip("#")
    if len(v) != 6:
        raise ValueError(f"Warna hex tidak valid: {value!r}")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def _relative_luminance(value: str) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = _hex_to_rgb(value)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """Rasio kontras WCAG 2.x antara dua warna hex."""
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def css_variables(palette: Dict[str, str]) -> str:
    """Blok deklarasi `--dl-*` untuk satu palet."""
    return "".join(
        f"  --dl-{name.replace('_', '-')}: {value};\n"
        for name, value in palette.items()
    )


def css_variables_auto(light: Dict[str, str], dark: Dict[str, str]) -> str:
    """Blok `--dl-*` memakai `light-dark()`.

    Streamlit memasang `color-scheme: light|dark` pada `.stApp` sesuai tema
    aktif, sehingga `light-dark()` memilih nilai yang benar dan langsung
    berubah saat pengguna mengganti tema, tanpa rerun.
    """
    return "".join(
        f"  --dl-{name.replace('_', '-')}: "
        f"light-dark({light[name]}, {dark[name]});\n"
        for name in light
    )


def normalize_mode(mode: Optional[str]) -> Optional[str]:
    """'light' | 'dark' | None (ikuti tema aktif Streamlit)."""
    return mode if mode in PALETTES else None


def build_css(mode: Optional[str] = None) -> str:
    """CSS tambahan di atas tema `.streamlit/config.toml`.

    `mode` None (default) mengikuti tema aktif Streamlit lewat
    `light-dark()`; 'light'/'dark' memaksa satu palet.

    Selector `data-testid` / `.st-key-*` bergantung pada DOM Streamlit
    1.65; bila berubah, UI tetap berfungsi tanpa gaya tambahan ini.
    """
    mode = normalize_mode(mode)
    if mode is None:
        variables = (
            # Fallback statis untuk browser tanpa dukungan light-dark().
            f".stApp {{\n{css_variables(LIGHT)}}}\n"
            "@supports (color: light-dark(#000, #fff)) {\n"
            f".stApp {{\n{css_variables_auto(LIGHT, DARK)}}}\n}}\n"
        )
    else:
        variables = f".stApp {{\n{css_variables(PALETTES[mode])}}}\n"

    return f"""
<style>
{variables}
.stApp {{
  --dl-radius-sm: {RADIUS_SM}px;
  --dl-radius-md: {RADIUS_MD}px;
  --dl-radius-lg: {RADIUS_LG}px;
  --dl-mono: {FONT_MONO};
}}
.stApp, .stApp button, .stApp input, .stApp textarea {{
  font-family: {FONT_STACK};
}}
.stApp {{ font-size: {FONT_SIZE_BASE}px; }}
.sr-only {{
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}}
.stApp h1 {{ font-size: {FONT_SIZE_HEADING[1]}px; font-weight: 700; letter-spacing: -0.01em; }}
.stApp h2, .stApp h3 {{ font-size: {FONT_SIZE_HEADING[0]}px; font-weight: 650; letter-spacing: -0.005em; }}
.stApp h4 {{ font-size: 16px; font-weight: 650; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 2.5rem; max-width: 1180px; }}

/* Hero */
.dl-hero {{
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  padding: 20px 24px; margin-bottom: 12px;
  border: 1px solid var(--dl-border); border-radius: var(--dl-radius-lg);
  background: linear-gradient(135deg, var(--dl-accent-soft) 0%, var(--dl-violet-soft) 100%);
}}
.dl-logo {{
  width: 52px; height: 52px; flex: 0 0 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--dl-accent) 0%, var(--dl-violet) 100%);
  box-shadow: 0 6px 16px var(--dl-shadow);
}}
.dl-hero-text {{ flex: 1 1 260px; min-width: 0; }}
.dl-hero-title {{ font-size: 26px; font-weight: 750; color: var(--dl-text); line-height: 1.2; letter-spacing: -0.02em; }}
.dl-hero-title .dl-grad {{
  background: linear-gradient(90deg, var(--dl-accent), var(--dl-violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}}
.dl-hero-sub {{ color: var(--dl-secondary); margin-top: 2px; }}
.dl-hero-badges {{ display: flex; gap: 8px; flex-wrap: wrap; }}

/* Status bar */
.dl-statusbar {{
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  padding: 10px 14px; margin-bottom: 4px;
  background: var(--dl-surface); border: 1px solid var(--dl-border);
  border-radius: var(--dl-radius-md); color: var(--dl-text);
}}
.dl-statusbar .dl-sep {{ color: var(--dl-secondary); }}
.dl-statusbar .dl-file {{ font-weight: 650; }}

/* Stepper */
.dl-stepper {{
  display: flex; list-style: none; margin: 8px 0 16px; padding: 14px 8px 10px;
  background: var(--dl-surface); border: 1px solid var(--dl-border);
  border-radius: var(--dl-radius-md);
}}
.dl-stepper li {{
  flex: 1 1 0; min-width: 0; position: relative; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}}
.dl-stepper li + li::before {{
  content: ""; position: absolute; top: 14px; right: calc(50% + 20px);
  left: calc(-50% + 20px); height: 2px; background: var(--dl-border);
}}
.dl-stepper li.dl-done + li::before {{ background: var(--dl-success); }}
.dl-step-dot {{
  width: 28px; height: 28px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; font-size: 13px; font-weight: 700;
  border: 2px solid var(--dl-border); background: var(--dl-surface); color: var(--dl-secondary);
}}
.dl-done .dl-step-dot {{ border-color: var(--dl-success); background: var(--dl-success-soft); color: var(--dl-success-text); }}
.dl-current .dl-step-dot {{
  border-color: var(--dl-accent); background: var(--dl-accent); color: var(--dl-on-accent);
  box-shadow: 0 0 0 4px var(--dl-accent-soft);
}}
.dl-step-name {{ font-weight: 600; font-size: 13px; color: var(--dl-text); }}
.dl-current .dl-step-name {{ color: var(--dl-accent); }}
.dl-step-sub {{ font-size: 12px; color: var(--dl-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; padding: 0 4px; }}

/* Pill / badge */
.dl-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 8px; }}
.dl-pill {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 10px; border-radius: 999px; border: 1px solid;
  font-size: 12px; font-weight: 550; line-height: 18px; white-space: nowrap;
}}
.dl-pill .dl-ico {{ font-size: 11px; }}
.dl-tone-neutral {{ color: var(--dl-text); background: var(--dl-neutral-soft); border-color: var(--dl-border); }}
.dl-tone-muted   {{ color: var(--dl-muted-text); background: var(--dl-neutral-soft); border-color: var(--dl-border); }}
.dl-tone-accent  {{ color: var(--dl-accent); background: var(--dl-accent-soft); border-color: var(--dl-accent); }}
.dl-tone-success {{ color: var(--dl-success-text); background: var(--dl-success-soft); border-color: var(--dl-success); }}
.dl-tone-warning {{ color: var(--dl-warning-text); background: var(--dl-warning-soft); border-color: var(--dl-warning); }}
.dl-tone-danger  {{ color: var(--dl-danger-text); background: var(--dl-danger-soft); border-color: var(--dl-danger); }}

/* Tab stage (Streamlit 1.65: [role=tablist] > [data-testid=stTab]) */
[data-testid="stTabs"] [role="tablist"] {{
  gap: 4px; padding: 4px; background: var(--dl-neutral-soft);
  border-radius: 12px; border: 1px solid var(--dl-border);
  overflow-x: auto; scrollbar-width: none;
}}
[data-testid="stTabs"] [role="tablist"]::after {{ display: none; }}
[data-testid="stTab"] {{
  height: 38px; padding: 0 14px !important; border-radius: 9px;
  color: var(--dl-secondary); font-weight: 600; border: 0 !important;
}}
[data-testid="stTab"]:hover {{ color: var(--dl-text); }}
[data-testid="stTab"][aria-selected="true"] {{
  background: var(--dl-surface); color: var(--dl-accent);
  box-shadow: 0 1px 3px var(--dl-shadow);
}}
[data-testid="stTab"] * {{ border-bottom: 0 !important; }}

/* Metric tile */
[data-testid="stMetric"] {{
  background: var(--dl-surface); border-radius: 12px !important;
}}
[data-testid="stMetricValue"] {{ font-weight: 700; letter-spacing: -0.02em; }}
[data-testid="stMetricLabel"] p {{ color: var(--dl-secondary); font-weight: 550; }}

/* Uploader */
[data-testid="stFileUploaderDropzone"] {{
  border: 2px dashed var(--dl-accent); background: var(--dl-surface);
  border-radius: var(--dl-radius-lg); padding: 18px 20px;
  transition: background .15s ease;
}}
[data-testid="stFileUploaderDropzone"]:hover {{ background: var(--dl-accent-soft); }}

/* Finding card */
[class*="st-key-fcard_"] {{
  background: var(--dl-surface); border-radius: 12px !important;
  transition: box-shadow .15s ease, transform .15s ease;
}}
[class*="st-key-fcard_"]:hover {{ box-shadow: 0 4px 14px var(--dl-shadow); }}
[class*="st-key-fcard_"]:has([data-testid="stCheckbox"] input:checked) {{
  border-left: 4px solid var(--dl-accent) !important;
  background: var(--dl-accent-soft);
}}
.dl-card-title {{ font-weight: 700; font-size: 16px; color: var(--dl-text); }}
.dl-card-arrow {{ color: var(--dl-secondary); margin: 0 6px; }}
.dl-card-suggest {{ color: var(--dl-success-text); font-weight: 700; }}
.dl-muted {{ color: var(--dl-secondary); font-size: 13px; }}
.dl-mono {{ font-family: var(--dl-mono); font-size: 12px; color: var(--dl-secondary); }}

/* Banner */
.dl-banner {{
  padding: 12px 16px; border-radius: var(--dl-radius-md);
  border: 1px solid; border-left-width: 4px; margin: 8px 0;
}}
.dl-banner-title {{ font-weight: 700; margin-bottom: 2px; }}

/* Empty state */
.dl-empty {{
  text-align: center; padding: 28px 16px; color: var(--dl-secondary);
  border: 1px dashed var(--dl-border); border-radius: var(--dl-radius-md);
  background: var(--dl-surface);
}}
.dl-empty-title {{ color: var(--dl-text); font-weight: 650; margin-bottom: 4px; }}

/* Landing */
.dl-landing {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin-top: 12px; }}
.dl-feature {{
  background: var(--dl-surface); border: 1px solid var(--dl-border);
  border-radius: var(--dl-radius-md); padding: 16px;
}}
.dl-feature-ico {{
  width: 36px; height: 36px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; margin-bottom: 10px;
  background: var(--dl-accent-soft); color: var(--dl-accent);
}}
.dl-feature-title {{ font-weight: 650; color: var(--dl-text); margin-bottom: 2px; }}
.dl-feature-body {{ color: var(--dl-secondary); font-size: 13px; }}
.dl-steps-inline {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; color: var(--dl-secondary); font-size: 13px; margin: 14px 0 0; }}
.dl-steps-inline b {{ color: var(--dl-text); font-weight: 650; }}

/* Meta card */
.dl-meta {{ display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; }}
.dl-meta dt {{ color: var(--dl-secondary); }}
.dl-meta dd {{ margin: 0; color: var(--dl-text); font-weight: 550; word-break: break-all; }}

/* Tabel change plan */
.dl-table-wrap {{ max-height: 420px; overflow: auto; border: 1px solid var(--dl-border); border-radius: var(--dl-radius-md); }}
table.dl-table {{ width: 100%; border-collapse: collapse; font-size: 13px; background: var(--dl-surface); }}
table.dl-table th {{
  position: sticky; top: 0; background: var(--dl-neutral-soft); color: var(--dl-text);
  text-align: left; font-weight: 650; padding: 8px; border-bottom: 1px solid var(--dl-border);
}}
table.dl-table td {{ padding: 8px; border-bottom: 1px solid var(--dl-border); vertical-align: top; color: var(--dl-text); }}

/* Sticky filter bar. Streamlit 1.65 membungkus container dalam
   stLayoutWrapper setinggi container itu sendiri, jadi sticky dipasang
   pada pembungkusnya. */
[data-testid="stLayoutWrapper"]:has(> .st-key-review_filter_bar),
.st-key-review_filter_bar {{
  position: sticky; top: 3.75rem; z-index: 20;
  background: var(--dl-bg);
}}
.st-key-review_filter_bar {{
  padding: 8px 0; border-bottom: 1px solid var(--dl-border);
}}

/* Sidebar */
[data-testid="stSidebar"] {{ border-right: 1px solid var(--dl-border); }}
.dl-brand {{ display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }}
.dl-brand .dl-logo {{ width: 36px; height: 36px; flex-basis: 36px; border-radius: 10px; box-shadow: none; }}
.dl-brand-name {{ font-size: 20px; font-weight: 750; color: var(--dl-text); letter-spacing: -0.02em; }}
.dl-side-list {{ list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }}
.dl-side-list li {{ display: flex; justify-content: space-between; gap: 8px; align-items: center; font-size: 13px; color: var(--dl-text); }}

/* Footer */
.dl-footer {{ margin-top: 32px; padding-top: 12px; border-top: 1px solid var(--dl-border); color: var(--dl-secondary); font-size: 12px; text-align: center; }}
</style>
"""


def inject_theme() -> None:
    """Sisipkan CSS sekali per render; warna mengikuti tema aktif.

    `st.context.theme` sengaja tidak dipakai: nilainya bisa keliru saat
    halaman pertama dimuat dan saat tema diganti (Streamlit #11920).
    """
    import streamlit as st

    st.markdown(build_css(None), unsafe_allow_html=True)


__all__ = [
    "LIGHT", "DARK", "COLORS", "PALETTES", "SPACING", "RADIUS_SM",
    "RADIUS_MD", "RADIUS_LG", "FONT_STACK", "FONT_MONO", "FONT_SIZE_BASE",
    "FONT_SIZE_HEADING", "TEXT_PAIRS", "build_css", "contrast_ratio",
    "css_variables", "css_variables_auto", "inject_theme", "normalize_mode",
]
