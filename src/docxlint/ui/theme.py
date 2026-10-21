"""Design tokens dan injeksi CSS (Phase 7.5).

Token dan helper kontras bersifat murni (tanpa Streamlit) agar dapat
ditest. Hanya `inject_theme()` yang menyentuh Streamlit.
"""

from typing import Dict, Tuple

# --- Warna -----------------------------------------------------------------
# `*_text` adalah varian gelap untuk teks di atas surface putih agar
# kontras >= 4.5:1 (WCAG AA). Warna dasar dipakai untuk border/aksen.
COLORS: Dict[str, str] = {
    "bg": "#FAFAFA",
    "surface": "#FFFFFF",
    "border": "#E5E7EB",
    "text": "#111827",
    "secondary": "#6B7280",
    "muted_text": "#4B5563",
    "accent": "#2563EB",
    "accent_soft": "#EFF6FF",
    "success": "#059669",
    "success_text": "#047857",
    "success_soft": "#ECFDF5",
    "warning": "#D97706",
    "warning_text": "#B45309",
    "warning_soft": "#FFFBEB",
    "danger": "#DC2626",
    "danger_text": "#B91C1C",
    "danger_soft": "#FEF2F2",
    "neutral_soft": "#F3F4F6",
}

SPACING: Tuple[int, ...] = (4, 8, 12, 16, 24, 32)
RADIUS_SM = 6
RADIUS_MD = 8
FONT_STACK = (
    'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", '
    "Arial, sans-serif"
)
FONT_MONO = (
    'ui-monospace, SFMono-Regular, "Cascadia Mono", Consolas, '
    '"Liberation Mono", monospace'
)
FONT_SIZE_BASE = 14
FONT_SIZE_HEADING = (20, 24)

# Pasangan (teks, latar) yang benar-benar dipakai UI untuk teks.
TEXT_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("text", "surface"),
    ("text", "bg"),
    ("secondary", "surface"),
    ("secondary", "bg"),
    ("accent", "surface"),
    ("accent", "accent_soft"),
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


def build_css() -> str:
    """CSS tambahan di atas tema `.streamlit/config.toml`.

    Selector `.st-key-*` bergantung pada kelas yang dibuat Streamlit untuk
    container ber-`key`; bila berubah, UI tetap berfungsi tanpa gaya ini.
    """
    c = COLORS
    return f"""
<style>
:root {{
  --dl-bg: {c['bg']};
  --dl-surface: {c['surface']};
  --dl-border: {c['border']};
  --dl-text: {c['text']};
  --dl-secondary: {c['secondary']};
  --dl-accent: {c['accent']};
  --dl-accent-soft: {c['accent_soft']};
  --dl-radius-sm: {RADIUS_SM}px;
  --dl-radius-md: {RADIUS_MD}px;
  --dl-mono: {FONT_MONO};
}}
.stApp, .stApp button, .stApp input, .stApp textarea {{
  font-family: {FONT_STACK};
}}
.stApp {{ font-size: {FONT_SIZE_BASE}px; }}
.stApp h1 {{ font-size: {FONT_SIZE_HEADING[1]}px; font-weight: 650; }}
.stApp h2, .stApp h3 {{ font-size: {FONT_SIZE_HEADING[0]}px; font-weight: 600; }}

/* Status bar */
.dl-statusbar {{
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  padding: 8px 12px; margin-bottom: 8px;
  background: var(--dl-surface); border: 1px solid var(--dl-border);
  border-radius: var(--dl-radius-md); color: var(--dl-text);
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04);
}}
.dl-statusbar .dl-sep {{ color: var(--dl-secondary); }}
.dl-statusbar .dl-file {{ font-weight: 600; }}

/* Pill / badge */
.dl-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 8px; }}
.dl-pill {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 999px; border: 1px solid;
  font-size: 12px; font-weight: 500; line-height: 18px;
  white-space: nowrap;
}}
.dl-pill .dl-ico {{ font-size: 11px; }}
.dl-tone-neutral {{ color: {c['text']}; background: {c['neutral_soft']}; border-color: {c['border']}; }}
.dl-tone-muted   {{ color: {c['muted_text']}; background: {c['neutral_soft']}; border-color: {c['border']}; }}
.dl-tone-accent  {{ color: {c['accent']}; background: {c['accent_soft']}; border-color: {c['accent']}; }}
.dl-tone-success {{ color: {c['success_text']}; background: {c['success_soft']}; border-color: {c['success']}; }}
.dl-tone-warning {{ color: {c['warning_text']}; background: {c['warning_soft']}; border-color: {c['warning']}; }}
.dl-tone-danger  {{ color: {c['danger_text']}; background: {c['danger_soft']}; border-color: {c['danger']}; }}

/* Finding card */
.dl-card-title {{ font-weight: 650; font-size: 15px; color: var(--dl-text); }}
.dl-card-arrow {{ color: var(--dl-secondary); margin: 0 6px; }}
.dl-card-suggest {{ color: {c['success_text']}; font-weight: 600; }}
.dl-muted {{ color: var(--dl-secondary); font-size: 13px; }}
.dl-mono {{ font-family: var(--dl-mono); font-size: 12px; color: var(--dl-secondary); }}
[class*="st-key-fcard_"]:has([data-testid="stCheckbox"] input:checked) {{
  border-left: 4px solid var(--dl-accent) !important;
  background: var(--dl-accent-soft);
}}

/* Banner */
.dl-banner {{
  padding: 12px 16px; border-radius: var(--dl-radius-md);
  border: 1px solid; border-left-width: 4px; margin: 8px 0;
}}
.dl-banner-title {{ font-weight: 650; margin-bottom: 2px; }}

/* Empty state */
.dl-empty {{
  text-align: center; padding: 24px 16px; color: var(--dl-secondary);
  border: 1px dashed var(--dl-border); border-radius: var(--dl-radius-md);
  background: var(--dl-surface);
}}
.dl-empty-title {{ color: var(--dl-text); font-weight: 600; margin-bottom: 4px; }}

/* Meta card */
.dl-meta {{ display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; }}
.dl-meta dt {{ color: var(--dl-secondary); }}
.dl-meta dd {{ margin: 0; color: var(--dl-text); font-weight: 500; word-break: break-all; }}

/* Tabel change plan */
.dl-table-wrap {{ max-height: 420px; overflow: auto; border: 1px solid var(--dl-border); border-radius: var(--dl-radius-md); }}
table.dl-table {{ width: 100%; border-collapse: collapse; font-size: 13px; background: var(--dl-surface); }}
table.dl-table th {{
  position: sticky; top: 0; background: {c['neutral_soft']}; color: var(--dl-text);
  text-align: left; font-weight: 600; padding: 8px; border-bottom: 1px solid var(--dl-border);
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

/* Checklist sidebar */
.dl-steps {{ list-style: none; padding: 0; margin: 0; }}
.dl-steps li {{ display: flex; gap: 8px; align-items: baseline; padding: 4px 0; }}
.dl-steps .dl-step-state {{ font-size: 12px; color: var(--dl-secondary); }}
</style>
"""


def inject_theme() -> None:
    """Sisipkan CSS sekali per render."""
    import streamlit as st

    st.markdown(build_css(), unsafe_allow_html=True)


__all__ = [
    "COLORS", "SPACING", "RADIUS_SM", "RADIUS_MD", "FONT_STACK",
    "FONT_MONO", "FONT_SIZE_BASE", "FONT_SIZE_HEADING", "TEXT_PAIRS",
    "build_css", "contrast_ratio", "inject_theme",
]
