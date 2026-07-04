import html
import streamlit as st
from lib.theme import ThemeManager

# ===================== Global Design Tokens =====================
BACKGROUND_PAGE = "#161B22"
CONTAINER_BG = "#161B22"
CONTAINER_BORDER = "#2C3440"
CONTAINER_RADIUS = 12
CONTAINER_PADDING = 16

SIDEBAR_BG = "#075D32"
SIDEBAR_TEXT = "#FFFFFF"

FILTER_BG = "#2AA666"
FILTER_TEXT = "#FFFFFF"
FILTER_RADIUS = 8

HEADER_BG = "#075D32"
HEADER_TEXT = "#FFFFFF"
HEADER_PADDING = 15
HEADER_RADIUS = 10

KPI_POSITIVE = "#1BBD6D"
KPI_NEGATIVE = "#D42E1B"
KPI_RADIUS = 12

POSITIVE_TEXT = "#1BBD6D"


def apply_page_frame():
    """Applies global layout container styling."""
    st.markdown(
        """
        <style>
        .bb-page-frame {
            background: #161B22;
            border: 1px solid #2C3440;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def green_banner(title: str):
    st.markdown(
        f"""
        <div style="background:{HEADER_BG}; color:{HEADER_TEXT}; padding:{HEADER_PADDING}px; border-radius:{HEADER_RADIUS}px; font-weight:800; margin-bottom:18px; width:100%; font-size:24px; line-height:1.25;">
            {title}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _tooltip_html(field: str, value: str) -> str:
    return f"<div style='margin:0 0 6px 0; line-height:1.3;'><span style='color:#A8E6B7; font-weight:700;'>{html.escape(field)} : </span><span style='color:#FFFFFF;'>{html.escape(str(value))}</span></div>"


def _ensure_premium_kpi_css() -> None:
    palette = ThemeManager.get_palette()
    shadow = '0 16px 36px rgba(15, 23, 42, 0.12)' if st.session_state.get('theme_mode', 'dark') == 'light' else '0 16px 36px rgba(0, 0, 0, 0.24)'
    st.markdown(
        f"""
        <style>
        .bb-premium-kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 16px; }}
        .bb-premium-kpi-card {{
            position: relative;
            overflow: visible;
            z-index: 1;
            background: {palette['surface']};
            border: 1px solid {palette['border']};
            border-radius: 22px;
            padding: 16px 18px;
            min-height: 150px;
            color: {palette['text_primary']};
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 10px;
            box-shadow: {shadow};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .bb-premium-kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 22px 44px rgba(15, 23, 42, 0.16); z-index: 10001; }}
        .bb-premium-kpi-header {{ display: flex; align-items: center; gap: 12px; }}
        .bb-premium-kpi-icon {{
            width: 52px; height: 52px; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: 900; color: #FFFFFF; flex-shrink: 0;
        }}
        .bb-premium-kpi-title {{ font-size: 0.78rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: {palette['text_secondary']}; margin: 0; }}
        .bb-premium-kpi-value {{ font-size: 1.7rem; font-weight: 900; line-height: 1.15; color: {palette['text_primary']}; margin: 4px 0 0; }}
        .bb-premium-kpi-subtitle {{ font-size: 0.84rem; color: {palette['text_muted']}; line-height: 1.35; margin: 0; }}
        .bb-premium-kpi-delta {{
            display: inline-flex; align-items: center; align-self: flex-start; padding: 7px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 700; background: {palette['surface_light']}; color: {palette['text_secondary']}; border: 1px solid {palette['border']};
        }}
        .bb-premium-kpi-tooltip {{
            display: none; position: absolute; top: calc(100% + 8px); left: 0; right: 0; z-index: 60; background: {palette['surface']}; border: 1px solid {palette['border']}; border-radius: 14px; padding: 10px 12px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
        }}
        .bb-premium-kpi-card:hover .bb-premium-kpi-tooltip {{ display: block; }}
        @media (max-width: 760px) {{ .bb-premium-kpi-card {{ min-height: auto; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _resolve_color(color: str | None, fallback: str) -> str:
    if not color:
        return fallback
    palette = ThemeManager.get_palette()
    if color in palette:
        return palette[color]
    return color


def kpi_card(
    label: str,
    value: str,
    tooltip_pairs: list[tuple[str, str]],
    delta: str | None = None,
    delta_color: str | None = None,
    icon: str | None = None,
    icon_color: str | None = None,
    subtitle: str | None = None,
):
    """Premium KPI card styled to match the ABC Analysis reference."""
    _ensure_premium_kpi_css()

    tooltip_html = "".join([_tooltip_html(f, v) for f, v in tooltip_pairs])
    icon_value = icon or '●'
    icon_bg = _resolve_color(icon_color, ThemeManager.get_palette()['positive'])
    delta_text = delta or subtitle or ''
    delta_html = ""
    if delta_text:
        palette = ThemeManager.get_palette()
        delta_html = f"<div class='bb-premium-kpi-delta' style='background:{palette['surface_light']}; color:{palette['text_primary']};'>{html.escape(str(delta_text))}</div>"
    subtitle_text = subtitle or (delta if delta is not None else '')
    if not subtitle_text and tooltip_pairs:
        subtitle_text = tooltip_pairs[0][1]

    st.markdown(
        f"""
        <div class="bb-premium-kpi-card">
          <div class="bb-premium-kpi-header">
            <div class="bb-premium-kpi-icon" style="background:{icon_bg};">{html.escape(str(icon_value))}</div>
            <div>
              <p class="bb-premium-kpi-title">{html.escape(str(label))}</p>
              <p class="bb-premium-kpi-value">{html.escape(str(value))}</p>
            </div>
          </div>
          <p class="bb-premium-kpi-subtitle">{html.escape(str(subtitle_text))}</p>
          {delta_html}
          <div class="bb-premium-kpi-tooltip">{tooltip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def css_for_filters():
    st.markdown(
        f"""
        <style>
        div[data-baseweb='select'] > div {{}}

        /* Streamlit multiselect backgrounds */
        div.stMultiSelect {{ background:{FILTER_BG}; color:{FILTER_TEXT}; border-radius:{FILTER_RADIUS}px; }}
        /* Streamlit selectbox */
        div.stSelectbox {{ background:{FILTER_BG}; color:{FILTER_TEXT}; border-radius:{FILTER_RADIUS}px; }}
        </style>

        """,
        unsafe_allow_html=True,
    )

