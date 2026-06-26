import streamlit as st


class ThemeManager:
    """Dark-only theme manager (single default dark theme)."""

    # Dark-only palette per spec
    DARK_PALETTE = {
        'background': '#0E1117',
        'surface': '#161B22',
        'surface_light': '#1F2937',

        'positive': '#1BBD6D',
        'positive_2': '#15A95F',
        'positive_3': '#149453',
        'positive_chart_1': '#1BBD6D',
        'positive_chart_2': '#15A95F',
        'positive_chart_3': '#0E9144',
        'positive_chart_4': '#05A154',

        'negative': '#D42E1B',

        'text_primary': '#FFFFFF',
        'text_secondary': '#D0D7DE',
        'text_muted': '#B6BBC4',

        'border': '#2C3440',

        'success': '#1BBD6D',
        'warning': '#FFA940',
        'danger': '#D42E1B',
        'info': '#1890FF',

        'chart_primary': '#1BBD6D',
        'chart_secondary': '#15A95F',
        'chart_tertiary': '#0E9144',
        'chart_bg': '#161B22',
        'chart_grid': '#2A3340',
    }

    @staticmethod
    def get_palette() -> dict:
        return ThemeManager.DARK_PALETTE

    @staticmethod
    def init_theme() -> None:
        # Ensure dark-only
        st.session_state['theme_mode'] = 'dark'

    @staticmethod
    def render_theme_toggle() -> None:
        # No toggle per spec
        return

    @staticmethod
    def apply_custom_css() -> None:
        palette = ThemeManager.get_palette()
        css = f"""
        <style>
            :root {{
                --bg-primary: {palette['background']};
                --bg-surface: {palette['surface']};
                --text-primary: {palette['text_primary']};
                --text-secondary: {palette['text_secondary']};
                --color-primary: {palette['positive']};
            }}

            body {{ background-color: {palette['background']} !important; }}

            /* Streamlit overrides */
            .main {{
                background-color: {palette['background']};
                color: {palette['text_primary']};
            }}

            div.block-container {{
                padding: 10px 16px 12px !important;
                max-width: 100%;
            }}
            section.main {{
                padding-left: 12px !important;
                padding-right: 12px !important;
            }}
            section[data-testid="stSidebar"] {{
                background-color: #075D32 !important;
                color: #FFFFFF !important;
                padding: 12px 12px 16px !important;
            }}
            section[data-testid="stSidebar"] * {{
                color: #FFFFFF !important;
            }}
            div[data-testid="stSidebarNav"] button[aria-selected="true"],
            div[data-testid="stSidebarNav"] a[aria-selected="true"] {{
                background-color: #2AA666 !important;
                color: #FFFFFF !important;
                border-radius: 8px;
            }}
            .stSidebar .stMultiSelect, .stSidebar .stSelectbox, .stSidebar .stDateInput {{
                background-color: #2AA666 !important;
                color: #FFFFFF !important;
                border-radius: 8px !important;
            }}
            .stSidebar .stMultiSelect label, .stSidebar .stSelectbox label, .stSidebar .stDateInput label {{
                color: #FFFFFF !important;
            }}

            div[data-testid="column"] {{
                padding-left: 8px !important;
                padding-right: 8px !important;
            }}
            div[data-testid="stColumns"], div.stColumns {{
                gap: 12px !important;
            }}
            div[data-testid="stVerticalBlock"] > .element-container {{
                margin-bottom: 10px !important;
            }}
            .element-container {{
                margin-bottom: 12px !important;
                padding-bottom: 0 !important;
            }}
            .css-1m4m2rd, .css-1x8cf1d, .css-13cep8v {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            .stMetric, div[data-testid="metric-container"] {{
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 8px !important;
                padding: 14px 16px !important;
                border-radius: 16px !important;
                background-color: #1F2937 !important;
                color: #FFFFFF !important;
                box-shadow: 0 12px 24px rgba(0,0,0,0.20) !important;
                text-align: center !important;
            }}
            div[data-testid="metric-container"] > div {{ width: 100% !important; }}
            div[data-testid="metric-container"] span, div[data-testid="metric-container"] div, div[data-testid="metric-container"] p {{
                color: #FFFFFF !important;
            }}
            .stMetric .css-1vq4p4l, .stMetric span, .stMetric div {{
                color: #FFFFFF !important;
            }}
            .stMetric span[data-testid="stMetricDelta"], div[data-testid="metric-container"] span[data-testid="stMetricDelta"] {{
                margin-top: 10px !important;
                width: 100% !important;
                background: #000000 !important;
                padding: 10px 12px !important;
                border-radius: 12px !important;
                text-align: left !important;
                font-weight: 700 !important;
            }}
            .css-1y4p8pa, .css-1g6go3h, .css-18e3th9 {{
                margin-bottom: 10px !important;
            }}
            .stDataFrame, .element-container .stDataFrame {{
                border-radius: 14px !important;
                padding: 10px !important;
                background: #161B22 !important;
            }}
            .plotly-graph-div {{ background-color: transparent !important; }}
            .stMarkdown {{ margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }}
            .stDivider {{ margin: 10px 0 !important; }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

