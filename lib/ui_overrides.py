import streamlit as st

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
    return f"<div style='margin:0 0 6px 0; line-height:1.3;'><span style='color:#A8E6B7; font-weight:700;'>{field} : </span><span style='color:#FFFFFF;'>{value}</span></div>"


def kpi_card(
    label: str,
    value: str,
    tooltip_pairs: list[tuple[str, str]],
    delta: str | None = None,
    delta_color: str | None = None,
):
    """Power BI-like KPI card with hover tooltip."""

    tooltip_html = "".join([_tooltip_html(f, v) for f, v in tooltip_pairs])
    delta_html = ""
    if delta is not None:
        delta_html = f"""
        <div class='bb-kpi-delta'>
            <span>{delta}</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="bb-kpi-card">
          <div class="bb-kpi-label">{label}</div>
          <div class="bb-kpi-value">{value}</div>
          {delta_html}
          <div class="bb-kpi-tooltip">
            {tooltip_html}
          </div>
        </div>
        <style>
        .bb-kpi-card {{
            position: relative;
            background: #1F2937;
            border: 1px solid #2C3440;
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 14px 28px rgba(0,0,0,0.24);
            color: #FFFFFF;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 140px;
            gap: 10px;
        }}
        .bb-kpi-card .bb-kpi-label {{
            text-align: center;
            font-weight: 700;
            font-size: 0.95rem;
            opacity: 0.95;
            margin: 0;
        }}
        .bb-kpi-card .bb-kpi-value {{
            text-align: center;
            font-weight: 800;
            font-size: 2.1rem;
            line-height: 1.1;
            margin: 0;
        }}
        .bb-kpi-card .bb-kpi-delta {{
            margin-top: 10px;
            background: #000000;
            color: #FFFFFF;
            border-radius: 12px;
            padding: 10px 12px;
            text-align: left;
            width: 100%;
            font-weight: 700;
            line-height: 1.3;
        }}
        .bb-kpi-card .bb-kpi-tooltip {{
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            transform: translateY(10px);
            background: rgba(7,21,18,0.95);
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 12px;
            padding: 12px;
            z-index: 60;
            min-width: 220px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }}
        .bb-kpi-card:hover .bb-kpi-tooltip {{
            display: block;
        }}
        </style>
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

