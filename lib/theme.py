import streamlit as st


class ThemeManager:
    """Theme-aware palette manager with light and dark support."""

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

    LIGHT_PALETTE = {
        'background': '#F5F9FF',
        'surface': '#FFFFFF',
        'surface_light': '#F8FBFF',
        'positive': '#0E7C5E',
        'positive_2': '#149C6A',
        'positive_3': '#1BA76B',
        'positive_chart_1': '#0E7C5E',
        'positive_chart_2': '#149C6A',
        'positive_chart_3': '#1BA76B',
        'positive_chart_4': '#2FC07E',
        'negative': '#D42E1B',
        'text_primary': '#0F172A',
        'text_secondary': '#334155',
        'text_muted': '#64748B',
        'border': '#D9E7F7',
        'success': '#16A34A',
        'warning': '#F59E0B',
        'danger': '#DC2626',
        'info': '#2563EB',
        'chart_primary': '#0E7C5E',
        'chart_secondary': '#149C6A',
        'chart_tertiary': '#1BA76B',
        'chart_bg': '#FFFFFF',
        'chart_grid': '#E2E8F0',
    }

    @staticmethod
    def get_palette() -> dict:
        theme_mode = st.session_state.get('theme_mode', 'dark')
        return ThemeManager.LIGHT_PALETTE if theme_mode == 'light' else ThemeManager.DARK_PALETTE

    @staticmethod
    def init_theme() -> None:
        if 'theme_mode' not in st.session_state:
            st.session_state['theme_mode'] = 'dark'

    @staticmethod
    def render_theme_toggle() -> None:
        return

    @staticmethod
    def apply_custom_css() -> None:
        palette = ThemeManager.get_palette()
        is_dark = st.session_state.get('theme_mode', 'dark') == 'dark'
        shadow = '0 10px 24px rgba(15, 23, 42, 0.12)' if not is_dark else '0 12px 24px rgba(0, 0, 0, 0.20)'
        metric_bg = palette['surface_light']
        metric_text = palette['text_primary']
        border_color = palette['border']
        css = f"""
        <style>
            :root {{
                --bg-primary: {palette['background']};
                --bg-surface: {palette['surface']};
                --bg-surface-light: {palette['surface_light']};
                --text-primary: {palette['text_primary']};
                --text-secondary: {palette['text_secondary']};
                --text-muted: {palette['text_muted']};
                --color-primary: {palette['positive']};
                --border-color: {border_color};
            }}

            body {{ background-color: {palette['background']} !important; }}

            .main {{
                background-color: {palette['background']};
                color: {palette['text_primary']};
            }}

            div.block-container {{
                padding: 10px 14px 12px !important;
                max-width: 100%;
            }}
            section.main {{
                padding-left: 10px !important;
                padding-right: 10px !important;
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
                padding-left: 6px !important;
                padding-right: 6px !important;
            }}
            div[data-testid="stColumns"], div.stColumns {{
                gap: 10px !important;
            }}
            div[data-testid="stVerticalBlock"] > .element-container {{
                margin-bottom: 8px !important;
            }}
            .element-container {{
                margin-bottom: 10px !important;
                padding-bottom: 0 !important;
            }}
            .css-1m4m2rd, .css-1x8cf1d, .css-13cep8v {{
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            .dashboard-shell {{
                background: {palette['surface']};
                border: 1px solid {border_color};
                border-radius: 22px;
                padding: 16px 16px 18px;
                box-shadow: {shadow};
                margin-top: 4px;
            }}
            .dashboard-card {{
                background: {palette['surface_light']};
                border: 1px solid {border_color};
                border-radius: 16px;
                padding: 12px 14px;
                margin-top: 10px;
            }}
            .dashboard-title-block h1 {{
                font-size: 1.35rem !important;
                margin-bottom: 0.15rem !important;
            }}
            .dashboard-title-block p, .dashboard-title-block div {{
                font-size: 0.95rem !important;
                color: {palette['text_secondary']} !important;
            }}
            .dashboard-timestamp {{
                font-size: 0.82rem !important;
                color: {palette['text_secondary']};
                text-align: right;
                line-height: 1.35;
            }}
            .dashboard-chip {{
                background: {palette['surface_light']};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 8px 10px;
                font-size: 0.84rem;
                color: {palette['text_secondary']};
                min-height: 42px;
            }}
            .compact-section h3, .compact-section h4 {{
                font-size: 1rem !important;
                margin-bottom: 0.35rem !important;
            }}
            .compact-section p, .compact-section li, .compact-section div {{
                font-size: 0.84rem !important;
                line-height: 1.35;
            }}
            .stMetric, div[data-testid="metric-container"] {{
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 6px !important;
                padding: 12px 14px !important;
                border-radius: 14px !important;
                background-color: {metric_bg} !important;
                color: {metric_text} !important;
                border: 1px solid {border_color} !important;
                box-shadow: {shadow} !important;
                text-align: center !important;
            }}
            div[data-testid="metric-container"] > div {{ width: 100% !important; }}
            div[data-testid="metric-container"] span, div[data-testid="metric-container"] div, div[data-testid="metric-container"] p {{
                color: {metric_text} !important;
            }}
            .stMetric .css-1vq4p4l, .stMetric span, .stMetric div {{
                color: {metric_text} !important;
            }}
            .stMetric span[data-testid="stMetricDelta"], div[data-testid="metric-container"] span[data-testid="stMetricDelta"] {{
                margin-top: 6px !important;
                width: 100% !important;
                background: {palette['surface']} !important;
                padding: 8px 10px !important;
                border-radius: 10px !important;
                text-align: left !important;
                font-weight: 600 !important;
            }}
            .css-1y4p8pa, .css-1g6go3h, .css-18e3th9 {{
                margin-bottom: 8px !important;
            }}
            .stDataFrame, .element-container .stDataFrame {{
                border-radius: 12px !important;
                padding: 8px !important;
                background: {palette['surface']} !important;
            }}
            .plotly-graph-div {{ background-color: transparent !important; }}
            .stMarkdown {{ margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }}
            .stDivider {{ margin: 8px 0 !important; }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

