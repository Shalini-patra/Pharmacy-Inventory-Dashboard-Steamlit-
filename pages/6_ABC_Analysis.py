import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.ui_overrides import green_banner

st.set_page_config(page_title="ABC Analysis", page_icon="📈", layout="wide")
ThemeManager.init_theme()
ThemeManager.apply_custom_css()

palette = ThemeManager.get_palette()
chart_colors = ColorPalette.get_chart_colors()
abc_colors = ColorPalette.get_abc_colors()

if 'selected_abc_class' not in st.session_state:
    st.session_state.selected_abc_class = None


def safe_int(val, default=0):
    """Safely convert value to integer, handling NaN and other errors."""
    try:
        if pd.isna(val):
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def format_inr(value):
    try:
        return f"₹ {float(value):,.0f}"
    except (TypeError, ValueError):
        return "₹ 0"


def page_styles():
    st.markdown(
        f"""
        <style>
        .bb-section-title {{ font-size: 1.36rem; margin-bottom: 18px; font-weight: 800; color: {palette['text_primary']}; }}
        .bb-top-kpi-row {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .bb-top-kpi-card {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 22px;
            min-height: 210px;
            color: {palette['text_primary']};
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 14px;
            box-shadow: 0 18px 40px rgba(0,0,0,0.24);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}
        .bb-top-kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 22px 56px rgba(0,0,0,0.24); }}
        .bb-top-kpi-card--clickable {{ cursor: pointer; }}
        .bb-top-kpi-icon {{ width: 56px; height: 56px; border-radius: 18px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.45rem; font-weight: 900; color: #FFFFFF; }}
        .bb-top-kpi-title {{ font-size: 0.95rem; letter-spacing: 0.04em; text-transform: uppercase; opacity: 0.9; margin: 0; }}
        .bb-top-kpi-value {{ font-size: 2.2rem; font-weight: 800; margin: 0; }}
        .bb-top-kpi-meta {{ color: {palette['text_secondary']}; font-size: 0.95rem; margin-top: 6px; }}
        .bb-top-kpi-note {{ color: {palette['text_secondary']}; font-size: 0.88rem; line-height: 1.5; }}
        .bb-action-button button {{ width: 100% !important; background: rgba(255,255,255,0.08) !important; color: {palette['text_primary']} !important; border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 14px !important; padding: 12px 16px !important; font-weight: 700 !important; transition: background 0.2s ease !important; }}
        .bb-action-button button:hover {{ background: rgba(255,255,255,0.12) !important; }}
        .bb-guide-panel {{ border-radius: 24px; background: rgba(255,255,255,0.04); border: 1px solid rgba(59,130,246,0.20); padding: 28px; text-align: center; color: {palette['text_primary']}; margin-bottom: 16px; }}
        .bb-guide-panel .bb-guide-icon {{ font-size: 2rem; margin-bottom: 10px; }}
        .bb-guide-panel h2 {{ margin: 0; font-size: 1.5rem; letter-spacing: 0.03em; }}
        .bb-guide-panel p {{ margin: 14px auto 0; max-width: 720px; color: {palette['text_secondary']}; font-size: 1rem; line-height: 1.7; }}
        .bb-flowchart-wrapper {{ display: flex; justify-content: center; align-items: center; flex-direction: column; margin-bottom: 24px; }}
        .bb-flowchart-line {{ position: relative; width: calc(100% - 120px); height: 1px; background: rgba(255,255,255,0.16); margin: 0 auto; }}
        .bb-flowchart-links {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; width: 100%; max-width: 1060px; margin-top: 24px; }}
        .bb-flowchart-link {{ position: relative; display: flex; justify-content: center; }}
        .bb-flowchart-link::before {{ content: ''; position: absolute; top: -24px; width: 2px; height: 24px; background: currentColor; }}
        .bb-flowchart-node {{ background: {palette['surface_light']}; border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 18px 20px; min-width: 140px; color: {palette['text_primary']}; font-weight: 700; text-align: center; }}
        .bb-flowchart-link--a {{ color: #FF6B6B; }}
            .bb-flowchart-link--b {{ color: #FFA940; }}
        .bb-flowchart-link--c {{ color: #5DD27D; }}
        .bb-flowchart-link--a::before {{ left: calc(50% - 8px); }}
        .bb-flowchart-link--b::before {{ left: calc(50% - 8px); }}
        .bb-flowchart-link--c::before {{ left: calc(50% - 8px); }}
        .bb-premium-info-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin-top: 22px; }}
        .bb-premium-info-card {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 24px; box-shadow: 0 18px 40px rgba(0,0,0,0.18); transition: transform 0.25s ease, box-shadow 0.25s ease; }}
        .bb-premium-info-card:hover {{ transform: translateY(-3px); box-shadow: 0 22px 52px rgba(0,0,0,0.22); }}
        .bb-premium-info-card-header {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }}
        .bb-premium-icon {{ width: 64px; height: 64px; border-radius: 18px; display: flex; align-items: center; justify-content: center; font-size: 1.9rem; color: #FFFFFF; font-weight: 900; }}
        .bb-premium-card-title {{ margin: 0; font-size: 1.28rem; font-weight: 900; color: {palette['text_primary']}; }}
        .bb-premium-badge {{ display: inline-flex; align-items: center; justify-content: center; padding: 10px 14px; border-radius: 999px; font-size: 0.85rem; font-weight: 700; color: #FFFFFF; }}
        .bb-premium-summary {{ font-size: 1rem; margin: 12px 0 8px; font-weight: 700; color: {palette['text_primary']}; }}
        .bb-star-row {{ margin: 0 0 18px; font-size: 1.1rem; color: #FFD166; letter-spacing: 0.03em; }}
        .bb-info-block {{ display: grid; grid-template-columns: 36px 1fr; gap: 12px 12px; align-items: flex-start; margin-bottom: 14px; }}
        .bb-info-block-icon {{ width: 36px; height: 36px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.08); color: {palette['text_primary']}; }}
        .bb-info-block-title {{ margin: 0; font-size: 0.98rem; font-weight: 700; color: {palette['text_primary']}; }}
        .bb-info-block-copy {{ margin: 4px 0 0; color: {palette['text_secondary']}; font-size: 0.92rem; line-height: 1.55; }}
        .bb-recommendation-box {{ border-radius: 18px; padding: 18px; background: rgba(63,163,255,0.08); border: 1px solid rgba(63,163,255,0.16); color: {palette['text_secondary']}; margin-top: 18px; }}
        .bb-card-accent-a {{ background: #FF6B6B; }}
        .bb-card-accent-b {{ background: #FFA940; }}
        .bb-card-accent-c {{ background: #5DD27D; }}
        .bb-badge-a {{ background: rgba(255,107,107,0.15); color: #FF8A80; }}
        .bb-badge-b {{ background: rgba(255,169,64,0.15); color: #FFC26A; }}
        .bb-badge-c {{ background: rgba(93,210,125,0.15); color: #A6E9A9; }}
        .bb-shared-text {{ color: {palette['text_secondary']}; }}
        @media (max-width: 1110px) {{ .bb-top-kpi-row, .bb-flowchart-links, .bb-premium-info-grid {{ grid-template-columns: 1fr; }} }}
        @media (max-width: 760px) {{ .bb-top-kpi-card {{ min-height: auto; }} .bb-flowchart-line {{ width: 100%; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_revenue_bar_chart(detail_df: pd.DataFrame, class_key: str) -> go.Figure:
    bars = detail_df.sort_values('revenue_share_pct', ascending=True)
    color = abc_colors.get(class_key, '#888888')
    fig = go.Figure(
        go.Bar(
            x=bars['revenue_share_pct'],
            y=bars['drug_name'],
            orientation='h',
            marker_color=color,
            hovertemplate='<b>%{y}</b><br>Revenue Share: %{x:.2f}%<extra></extra>',
        )
    )
    fig.update_layout(
        margin={'t': 14, 'r': 18, 'l': 120, 'b': 36},
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title='Revenue Share %', gridcolor='rgba(255,255,255,0.08)', zerolinecolor='rgba(255,255,255,0.10)', tickfont=dict(color=palette['text_primary']), title_font=dict(color=palette['text_primary']), showgrid=True),
        yaxis=dict(title='Drug Name', tickfont=dict(color=palette['text_primary']), title_font=dict(color=palette['text_primary'])),
        font=dict(color=palette['text_primary']),
    )
    return fig


def get_overlay_context(title: str):
    """Return a supported Streamlit overlay context manager for the current runtime."""
    if hasattr(st, 'dialog'):
        try:
            ctx = st.dialog(title)
            if hasattr(ctx, '__enter__'):
                return ctx
        except Exception:
            pass
    if hasattr(st, 'popover'):
        try:
            ctx = st.popover(title)
            if hasattr(ctx, '__enter__'):
                return ctx
        except Exception:
            pass
    return st.expander(title, expanded=True)


def render_class_popup(class_key: str):
    detail_df = DatabaseManager.get_abc_class_details(class_key)
    if detail_df.empty:
        st.warning("No drug-level details are available for this ABC class at this time.")
        return

    chart_df = detail_df.sort_values('revenue_share_pct', ascending=False).head(12)
    fig = build_revenue_bar_chart(chart_df, class_key)

    st.markdown(f"## CLASS {class_key} DRUG DETAILS")
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    detail_df_display = detail_df[
        ['drug_id', 'drug_name', 'generic_name', 'therapeutic_category', 'revenue', 'revenue_share_pct', 'abc_class', 'remaining_stock', 'suggested_reorder_quantity']
    ].copy()
    detail_df_display = detail_df_display.sort_values('revenue', ascending=False)
    detail_df_display['revenue'] = detail_df_display['revenue'].map(lambda x: format_inr(x))
    detail_df_display['revenue_share_pct'] = detail_df_display['revenue_share_pct'].map(lambda x: f"{x:.2f}%")
    detail_df_display = detail_df_display.rename(columns={
        'drug_id': 'Drug ID',
        'drug_name': 'Drug Name',
        'generic_name': 'Generic Name',
        'therapeutic_category': 'Therapeutic Category',
        'revenue': 'Revenue',
        'revenue_share_pct': 'Revenue Share %',
        'abc_class': 'ABC Class',
        'remaining_stock': 'Remaining Stock',
        'suggested_reorder_quantity': 'Suggested Reorder Quantity',
    })

    st.dataframe(detail_df_display.sort_values('Revenue', ascending=False), use_container_width=True)


def render_premium_card(class_key: str, title: str, value: str, subtitle: str, color: str, badge: str, summary: str, stars: str, info_blocks: list[tuple[str, str, str]], footer: str):
    accent_class = f"bb-card-accent-{class_key.lower()}"
    badge_class = f"bb-badge-{class_key.lower()}"
    blocks_html = ''.join(
        f"<div class='bb-info-block'><div class='bb-info-block-icon'>{icon}</div><div><p class='bb-info-block-title'>{heading}</p><p class='bb-info-block-copy'>{copy}</p></div></div>"
        for icon, heading, copy in info_blocks
    )
    st.markdown(
        f"""
        <div class='bb-premium-info-card'>
          <div class='bb-premium-info-card-header'>
            <div class='bb-premium-icon {accent_class}'>{class_key}</div>
            <div>
              <p class='bb-premium-card-title'>{title}</p>
              <div class='bb-premium-badge {badge_class}'>{badge}</div>
            </div>
          </div>
          <p class='bb-premium-summary'>{summary}</p>
          <p class='bb-star-row'>{stars}</p>
          {blocks_html}
          <div class='bb-recommendation-box'>{footer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    green_banner("📈 ABC Classification Analysis")
    page_styles()

    try:
        abc_data = DatabaseManager.get_abc_analysis()

        # Robustly obtain latest snapshot date: prefer explicit helper if available,
        # otherwise run a safe SQL fallback so deployments with different DB helper
        # signatures won't crash the page.
        latest_snapshot_fn = getattr(DatabaseManager, 'get_latest_inventory_snapshot_date', None)
        if callable(latest_snapshot_fn):
            snapshot_df = latest_snapshot_fn()
        else:
            snapshot_df = DatabaseManager._read_sql_safe(
                "SELECT MAX(CAST(snapshot_date AS DATE)) AS latest_snapshot_date FROM inventory_snapshots;"
            )
    except Exception as exc:
        st.error(f"❌ Failed to load ABC analysis data: {str(exc)}")
        return

    latest_date = None
    if not snapshot_df.empty and 'latest_snapshot_date' in snapshot_df.columns:
        latest_date = snapshot_df.iloc[0]['latest_snapshot_date']
    if latest_date is None or pd.isna(latest_date):
        latest_date = pd.Timestamp.now().date()

    class_rows = {str(row['abc_class']): row for _, row in abc_data.iterrows()} if not abc_data.empty else {}
    class_data = {
        'A': class_rows.get('A', {'num_drugs': 0, 'revenue_pct': 0}),
        'B': class_rows.get('B', {'num_drugs': 0, 'revenue_pct': 0}),
        'C': class_rows.get('C', {'num_drugs': 0, 'revenue_pct': 0}),
    }
    total_revenue = abc_data['total_revenue'].sum() if not abc_data.empty else 0

    st.markdown("<div class='bb-section-title'>ABC Metrics</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='bb-top-kpi-row'>
          <div class='bb-top-kpi-card bb-top-kpi-card--clickable' style='--accent:#FF6B6B;'>
            <div class='bb-top-kpi-icon' style='background:#FF6B6B;'>A</div>
            <div>
              <div class='bb-top-kpi-title'>CLASS A</div>
              <div class='bb-top-kpi-value'>{safe_int(class_data['A']['num_drugs'])} Drugs</div>
              <div class='bb-top-kpi-meta'>Top 20% Revenue</div>
            </div>
            <div class='bb-top-kpi-note'>Click to view all drugs belonging to Class A.</div>
          </div>
          <div class='bb-top-kpi-card bb-top-kpi-card--clickable' style='--accent:#FFA940;'>
            <div class='bb-top-kpi-icon' style='background:#FFA940;'>B</div>
            <div>
              <div class='bb-top-kpi-title'>CLASS B</div>
              <div class='bb-top-kpi-value'>{safe_int(class_data['B']['num_drugs'])} Drugs</div>
              <div class='bb-top-kpi-meta'>Next 30–50% Revenue</div>
            </div>
            <div class='bb-top-kpi-note'>Click to view all drugs belonging to Class B.</div>
          </div>
          <div class='bb-top-kpi-card bb-top-kpi-card--clickable' style='--accent:#5DD27D;'>
            <div class='bb-top-kpi-icon' style='background:#5DD27D;'>C</div>
            <div>
              <div class='bb-top-kpi-title'>CLASS C</div>
              <div class='bb-top-kpi-value'>{safe_int(class_data['C']['num_drugs'])} Drugs</div>
              <div class='bb-top-kpi-meta'>Remaining Revenue</div>
            </div>
            <div class='bb-top-kpi-note'>Click to view all drugs belonging to Class C.</div>
          </div>
          <div class='bb-top-kpi-card'>
            <div class='bb-top-kpi-icon' style='background:#7C3AED;'>₹</div>
            <div>
              <div class='bb-top-kpi-title'>TOTAL REVENUE</div>
              <div class='bb-top-kpi-value'>{format_inr(total_revenue)}</div>
              <div class='bb-top-kpi-meta'>100% Total Revenue</div>
            </div>
            <div class='bb-top-kpi-note'>All revenue from current ABC classification.</div>
          </div>
          <div class='bb-top-kpi-card'>
            <div class='bb-top-kpi-icon' style='background:#1472E4;'>📅</div>
            <div>
              <div class='bb-top-kpi-title'>AS OF DATE</div>
              <div class='bb-top-kpi-value'>{pd.to_datetime(latest_date).strftime('%d %b %Y')}</div>
              <div class='bb-top-kpi-meta'>Latest ABC Analysis</div>
            </div>
            <div class='bb-top-kpi-note'>Latest inventory snapshot date used for analysis.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3, gap='small')
    with col1:
        if st.button('View Class A details', key='abc_a_view', help='Click to view all drugs belonging to Class A.'):
            st.session_state.selected_abc_class = 'A'
        if st.session_state.selected_abc_class == 'A':
            with get_overlay_context('CLASS A DRUG DETAILS'):
                render_class_popup('A')
            st.session_state.selected_abc_class = None
    with col2:
        if st.button('View Class B details', key='abc_b_view', help='Click to view all drugs belonging to Class B.'):
            st.session_state.selected_abc_class = 'B'
        if st.session_state.selected_abc_class == 'B':
            with get_overlay_context('CLASS B DRUG DETAILS'):
                render_class_popup('B')
            st.session_state.selected_abc_class = None
    with col3:
        if st.button('View Class C details', key='abc_c_view', help='Click to view all drugs belonging to Class C.'):
            st.session_state.selected_abc_class = 'C'
        if st.session_state.selected_abc_class == 'C':
            with get_overlay_context('CLASS C DRUG DETAILS'):
                render_class_popup('C')
            st.session_state.selected_abc_class = None

    st.markdown(
        """
        <div class='bb-guide-panel'>
          <div class='bb-guide-icon'>📖</div>
          <h2>ABC CLASSIFICATION GUIDE</h2>
          <p>Inventory is categorized based on its revenue contribution and business impact.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='bb-flowchart-wrapper'>
          <div class='bb-flowchart-line'></div>
          <div class='bb-flowchart-links'>
            <div class='bb-flowchart-link bb-flowchart-link--a'><div class='bb-flowchart-node'>CLASS A</div></div>
            <div class='bb-flowchart-link bb-flowchart-link--b'><div class='bb-flowchart-node'>CLASS B</div></div>
            <div class='bb-flowchart-link bb-flowchart-link--c'><div class='bb-flowchart-node'>CLASS C</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='bb-section-title'>ABC Classification Details</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='bb-premium-info-grid'>
        </div>
        """,
        unsafe_allow_html=True,
    )

    info_col1, info_col2, info_col3 = st.columns(3, gap='large')
    with info_col1:
        render_premium_card(
            class_key='A',
            title='CLASS A',
            value='',
            subtitle='Top 20% Revenue',
            color='#FF6B6B',
            badge='Top 20% Revenue',
            summary='Business Critical Drugs',
            stars='★★★★★',
            info_blocks=[
                ('💰', 'Revenue Contribution', 'Top 20% of Total Revenue'),
                ('⭐', 'Business Importance', 'Highest Financial Impact'),
                ('📦', 'Inventory Strategy', 'Maintain Maximum Availability'),
                ('👁', 'Monitoring Level', 'Daily Monitoring'),
                ('🎯', 'Recommended Action', 'Highest Reorder Priority'),
            ],
            footer='Small number of drugs but very high business impact. Focus on availability and zero stock-outs.',
        )
    with info_col2:
        render_premium_card(
            class_key='B',
            title='CLASS B',
            value='',
            subtitle='Next 30–50% Revenue',
            color='#FFA940',
            badge='Next 30–50% Revenue',
            summary='Medium Business Impact',
            stars='★★★☆☆',
            info_blocks=[
                ('💰', 'Revenue Contribution', 'Next 30–50% of Total Revenue'),
                ('⭐', 'Business Importance', 'Moderate Financial Impact'),
                ('📦', 'Inventory Strategy', 'Balanced Stock Levels'),
                ('👁', 'Monitoring Level', 'Regular Monitoring'),
                ('🎯', 'Recommended Action', 'Standard Reorder Practices'),
            ],
            footer='Balanced inventory. Focus on efficiency and optimization.',
        )
    with info_col3:
        render_premium_card(
            class_key='C',
            title='CLASS C',
            value='',
            subtitle='Remaining Revenue',
            color='#5DD27D',
            badge='Remaining Revenue',
            summary='Routine Inventory Items',
            stars='★★☆☆☆',
            info_blocks=[
                ('💰', 'Revenue Contribution', 'Remaining low-value revenue'),
                ('⭐', 'Business Importance', 'Low individual revenue'),
                ('📦', 'Inventory Strategy', 'Simplified stock management'),
                ('👁', 'Monitoring Level', 'Periodic Monitoring'),
                ('🎯', 'Recommended Action', 'Simplified reorder process'),
            ],
            footer='Large number of drugs but low business impact. Focus on simplification and inventory cost optimization.',
        )


if __name__ == '__main__':
    main()
