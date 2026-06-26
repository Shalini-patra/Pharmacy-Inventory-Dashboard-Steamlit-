import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import plotly.express as px
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.session_state import SessionStateManager
from lib.ui_overrides import apply_page_frame, green_banner, kpi_card
from lib.executive_overview_filters import build_sidebar_filters
from lib.executive_overview_queries import (
    get_filtered_top_moving_drugs,
    get_filtered_bottom_moving_drugs,
    get_filtered_monthly_revenue_profit_trend,
    get_filtered_monthly_customer_metrics,
    get_filtered_weekday_hour_heatmap,
)

st.set_page_config(
    page_title="Executive Overview",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

ThemeManager.init_theme()
ThemeManager.apply_custom_css()
SessionStateManager.init_filters()

palette = ThemeManager.get_palette()
colors = ColorPalette.get_chart_colors()

apply_page_frame()
green_banner("Executive Overview")

st.markdown(
    f"<div style='margin-top:-8px; margin-bottom:16px; color:#D0D7DE; font-weight:600;'>"
    f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    f"</div>",
    unsafe_allow_html=True,
)

filters = build_sidebar_filters()

try:
    monthly_trend = get_filtered_monthly_revenue_profit_trend(filters, months=12)
    monthly_customers = get_filtered_monthly_customer_metrics(filters, months=12)
    top_drugs = get_filtered_top_moving_drugs(filters, days=30, limit=5)
    bottom_drugs = get_filtered_bottom_moving_drugs(filters, days=30, limit=5)
    heatmap_df = get_filtered_weekday_hour_heatmap(filters, months=12)

    if monthly_trend.empty:
        raise ValueError("No revenue data available for the selected filters.")

    monthly_trend = monthly_trend.sort_values("month")
    monthly_trend["profit_margin"] = monthly_trend.apply(
        lambda row: (row["total_profit"] / row["total_revenue"] * 100) if row["total_revenue"] else 0,
        axis=1,
    )
    monthly_trend["revenue_growth"] = monthly_trend["total_revenue"].pct_change().fillna(0) * 100

    current_rev = float(monthly_trend.iloc[-1]["total_revenue"])
    previous_rev = float(monthly_trend.iloc[-2]["total_revenue"]) if len(monthly_trend) > 1 else current_rev
    rev_growth = ((current_rev - previous_rev) / previous_rev * 100) if previous_rev else 0

    current_profit = float(monthly_trend.iloc[-1]["total_profit"])
    previous_profit = float(monthly_trend.iloc[-2]["total_profit"]) if len(monthly_trend) > 1 else current_profit
    profit_growth = ((current_profit - previous_profit) / previous_profit * 100) if previous_profit else 0

    if monthly_customers.empty:
        current_cust = 0
        cust_growth = 0
    else:
        monthly_customers = monthly_customers.sort_values("month")
        current_cust = int(monthly_customers.iloc[-1]["unique_customers"])
        previous_cust = int(monthly_customers.iloc[-2]["unique_customers"]) if len(monthly_customers) > 1 else current_cust
        cust_growth = ((current_cust - previous_cust) / previous_cust * 100) if previous_cust else 0

    regular_cust = DatabaseManager.get_regular_customers(min_transactions=5, days=90)
    regular_count = len(regular_cust) if regular_cust is not None else 0
    regular_pct = (regular_count / current_cust * 100) if current_cust else 0

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small")

    with col1:
        kpi_card(
            label="Monthly Revenue",
            value=f"₹{current_rev:,.0f}",
            tooltip_pairs=[
                ("Total Revenue", f"₹{current_rev:,.0f}"),
                ("MoM Growth", f"{rev_growth:+.1f}%"),
            ],
            delta=f"{rev_growth:+.1f}%",
            delta_color="#FFFFFF",
        )

    with col2:
        kpi_card(
            label="Monthly Profit",
            value=f"₹{current_profit:,.0f}",
            tooltip_pairs=[
                ("Total Profit", f"₹{current_profit:,.0f}"),
                ("MoM Growth", f"{profit_growth:+.1f}%"),
            ],
            delta=f"{profit_growth:+.1f}%",
            delta_color="#FFFFFF",
        )

    with col3:
        kpi_card(
            label="Unique Customers",
            value=f"{current_cust:,}",
            tooltip_pairs=[
                ("Unique Customers", f"{current_cust:,}"),
                ("MoM Growth", f"{cust_growth:+.1f}%"),
            ],
            delta=f"{cust_growth:+.1f}%",
            delta_color="#FFFFFF",
        )

    with col4:
        kpi_card(
            label="Regular Customers",
            value=f"{regular_pct:.1f}%",
            tooltip_pairs=[
                ("Repeat Customers", f"{regular_count}"),
                ("Filter Context", "Last 90 days"),
            ],
            delta=f"{regular_count} customers",
            delta_color="#FFFFFF",
        )

except Exception as e:
    st.error(f"❌ Error loading KPI and summary data: {str(e)}")
    monthly_trend = pd.DataFrame()
    monthly_customers = pd.DataFrame()
    top_drugs = pd.DataFrame()
    bottom_drugs = pd.DataFrame()
    heatmap_df = pd.DataFrame()

st.markdown("---")

st.subheader("Top & Bottom Performing Drugs (Last 30 Days)")

col1, col2 = st.columns([1, 1], gap="small")

with col1:
    st.markdown("<div style='color:#FFFFFF; font-size:18px; font-weight:700; margin-bottom:8px;'>🔥 Top 5 Moving Drugs</div>", unsafe_allow_html=True)
    if not top_drugs.empty:
        fig_top = px.bar(
            top_drugs,
            x="total_units",
            y="drug_name",
            orientation="h",
            color="total_units",
            color_continuous_scale=["#A0BEAF", "#05A154"],
            hover_data={
                "drug_name": True,
                "therapeutic_category": True,
                "total_units": True,
                "total_revenue": True,
                "abc_class": True,
            },
            labels={
                "total_units": "Total Units Sold",
                "drug_name": "Drug Name",
                "therapeutic_category": "Therapeutic Category",
                "total_revenue": "Total Revenue",
                "abc_class": "ABC Class",
            },
        )
        fig_top.update_layout(
            height=420,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=colors["text"]),
            xaxis_title="Total Units Sold",
            yaxis_title="",
            hovermode="closest",
            showlegend=True,
            margin=dict(l=0, r=0, t=20, b=20),
        )
        fig_top.update_xaxes(gridcolor=colors["grid"])
        fig_top.update_yaxes(gridcolor=colors["grid"], autorange="reversed")
        st.plotly_chart(fig_top, use_container_width=True)
        st.dataframe(
            top_drugs[["drug_name", "therapeutic_category", "total_units", "total_revenue", "abc_class"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No top moving drug data is available for the selected filters.")

with col2:
    st.markdown("<div style='color:#FFFFFF; font-size:18px; font-weight:700; margin-bottom:8px;'>📉 Bottom 5 Moving Drugs</div>", unsafe_allow_html=True)
    if not bottom_drugs.empty:
        fig_bottom = px.bar(
            bottom_drugs,
            x="total_units",
            y="drug_name",
            orientation="h",
            color="total_revenue",
            color_continuous_scale=["#EBD3D0", "#D42E1B"],
            hover_data={
                "drug_name": True,
                "therapeutic_category": True,
                "total_units": True,
                "total_revenue": True,
                "abc_class": True,
            },
            labels={
                "total_units": "Total Units Sold",
                "drug_name": "Drug Name",
                "therapeutic_category": "Therapeutic Category",
                "total_revenue": "Total Revenue",
                "abc_class": "ABC Class",
            },
        )
        fig_bottom.update_layout(
            height=420,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=colors["text"]),
            xaxis_title="Total Units Sold",
            yaxis_title="",
            hovermode="closest",
            showlegend=True,
            margin=dict(l=0, r=0, t=20, b=20),
        )
        fig_bottom.update_xaxes(gridcolor=colors["grid"])
        fig_bottom.update_yaxes(gridcolor=colors["grid"], autorange="reversed")
        st.plotly_chart(fig_bottom, use_container_width=True)
        st.dataframe(
            bottom_drugs[["drug_name", "therapeutic_category", "total_units", "total_revenue", "abc_class"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No bottom moving drug data is available for the selected filters.")

st.markdown("---")

st.markdown("<div style='color:#FFFFFF; font-size:18px; font-weight:700; margin-bottom:8px;'>Revenue vs Profit Trend</div>", unsafe_allow_html=True)
if not monthly_trend.empty:
    monthly_trend = monthly_trend.copy()
    monthly_trend["month"] = pd.to_datetime(monthly_trend["month"], errors="coerce")
    monthly_trend = monthly_trend.dropna(subset=["month"])
    monthly_trend["month_label"] = monthly_trend["month"].dt.strftime("%b %Y")
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_trend["month_label"],
            y=monthly_trend["total_revenue"],
            name="Revenue",
            mode="lines",
            line=dict(color="#119752", width=3),
            fill="tozeroy",
            fillcolor="rgba(17, 151, 82, 0.25)",
            hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<br>Profit: ₹%{customdata[0]:,.0f}<br>Profit Margin: %{customdata[1]:.1f}%<br>Growth: %{customdata[2]:.1f}%<extra></extra>",
            customdata=monthly_trend[["total_profit", "profit_margin", "revenue_growth"]].values,
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_trend["month_label"],
            y=monthly_trend["total_profit"],
            name="Profit",
            mode="lines",
            line=dict(color="#E44632", width=3),
            fill="tozeroy",
            fillcolor="rgba(228, 70, 50, 0.20)",
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Profit: ₹%{y:,.0f}<br>Revenue: ₹%{customdata[0]:,.0f}<br>Profit Margin: %{customdata[1]:.1f}%<extra></extra>",
            customdata=monthly_trend[["total_revenue", "profit_margin"]].values,
        )
    )
    fig_trend.update_layout(
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=colors["text"]),
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title="Revenue (₹)", gridcolor=colors["grid"]),
        yaxis2=dict(title="Profit (₹)", overlaying="y", side="right", gridcolor=colors["grid"]),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=20, b=40),
    )
    fig_trend.update_xaxes(gridcolor=colors["grid"])
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No revenue/profit trend data is available for the selected filters.")

st.markdown("---")

st.markdown("<div style='color:#FFFFFF; font-size:18px; font-weight:700; margin-bottom:8px;'>Orders by Weekday and Time of Day</div>", unsafe_allow_html=True)
if not heatmap_df.empty:
    pivot = heatmap_df.pivot_table(
        index="weekday",
        columns="hour_bin",
        values="transaction_count",
        aggfunc="sum",
    )
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hour_order = ["0-2", "2-4", "4-6", "6-8", "8-10", "10-12", "12-14", "14-16", "16-18", "18-20", "20-22", "22-24"]
    pivot = pivot.reindex(index=weekday_order, columns=hour_order).fillna(0)

    fig_heat = go.Figure()
    max_val = max(pivot.values.max(), 1)

    def get_color(value):
        normalized = value / max_val
        return px.colors.sample_colorscale(
            [[0.0, "#ABD0BD"], [1.0, "#05A154"]],
            normalized,
        )[0]

    for row_idx, weekday in enumerate(pivot.index):
        for col_idx, hour_bin in enumerate(pivot.columns):
            value = pivot.loc[weekday, hour_bin]

            fig_heat.add_shape(
                type="rect",
                x0=col_idx + 0.08,
                x1=col_idx + 0.92,
                y0=row_idx + 0.08,
                y1=row_idx + 0.92,
                fillcolor=get_color(value),
                line=dict(color="#1E293B", width=1),
            )

            fig_heat.add_trace(
                go.Scatter(
                    x=[col_idx + 0.5],
                    y=[row_idx + 0.5],
                    mode="markers",
                    marker=dict(size=0.1, color="rgba(0,0,0,0)"),
                    hovertemplate=
                        f"Weekday: {weekday}<br>"
                        f"Hour: {hour_bin}<br>"
                        f"Transactions: {int(value)}"
                        "<extra></extra>",
                    showlegend=False,
                )
            )

    fig_heat.update_layout(
        height=450,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=colors["text"]),
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(
            title="Time Window",
            tickmode="array",
            tickvals=[i + 0.5 for i in range(len(pivot.columns))],
            ticktext=list(pivot.columns),
            tickangle=-45,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="Weekday",
            tickmode="array",
            tickvals=[i + 0.5 for i in range(len(pivot.index))],
            ticktext=list(pivot.index),
            autorange="reversed",
            showgrid=False,
            zeroline=False,
        ),
        showlegend=False,
    )
    fig_heat.update_xaxes(range=[0, len(pivot.columns)], fixedrange=True)
    fig_heat.update_yaxes(range=[0, len(pivot.index)], fixedrange=True)
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No order activity heatmap data is available for the selected filters.")

st.markdown("---")
st.caption(f"Data updated from NeonDB every 5 minutes | Last sync: {datetime.now().strftime('%H:%M:%S')}")

