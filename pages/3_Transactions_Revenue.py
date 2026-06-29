import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.ui_overrides import green_banner
from plotly.subplots import make_subplots
import numpy as np
st.set_page_config(page_title="Transactions & Revenue", page_icon="💰", layout="wide")
ThemeManager.init_theme()
ThemeManager.apply_custom_css()


palette = ThemeManager.get_palette()
colors = ColorPalette.get_chart_colors()

green_banner("💰 Transactions & Revenue")

# ============== MONTHLY REVENUE BREAKDOWN ==============
try:
    profit_trend = DatabaseManager.get_profit_trend(days=365)
    
    # Aggregate by month
    profit_trend['year_month'] = pd.to_datetime(profit_trend['date']).dt.to_period('M')
    monthly_data = profit_trend.groupby('year_month').agg({
        'revenue': 'sum',
        'profit': 'sum',
        'cost': 'sum',
    }).reset_index()
    monthly_data['year_month'] = monthly_data['year_month'].astype(str)
    monthly_data["month_label"] = pd.to_datetime(
    monthly_data["year_month"]
    ).dt.strftime("%b")
    monthly_data = monthly_data.sort_values("year_month")
    
    # Create grouped bar chart
    max_profit = monthly_data["profit"].max()

    # Round up to a nice number
    axis_max = np.ceil(max_profit / 100000) * 100000

    # Create 6 evenly spaced ticks
    tickvals = np.linspace(-axis_max, 0, 6)

    # -----------------------------
    # Format labels
    # -----------------------------
    def format_axis(v):
        # Handle NaN values properly to prevent crashes
        try:
            if pd.isna(v):
                return "0"
        except (TypeError, ValueError):
            pass
        
        try:
            v = abs(v)
        except (TypeError, ValueError):
            return "0"

        if v >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        elif v >= 1000:
            return f"{v/1000:.0f}K"
        else:
            try:
                return f"{int(v)}"
            except (ValueError, TypeError):
                return "0"

    ticktext = [format_axis(v) for v in tickvals]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.00,
        row_heights=[0.5, 0.5]
    )
    
    fig.add_trace(
    go.Bar(
        x=monthly_data["month_label"],
        y=monthly_data["revenue"],
        marker_color="#05A154",
        hovertemplate="<b>%{x}</b><br>Revenue : ₹%{y:,.0f}<extra></extra>",
        showlegend=False,
        marker=dict(
            color="#05A154",
            line=dict(width=0)
        )
    ),
    row=1,
    col=1
    )
    

    fig.add_trace(
    go.Bar(
        x=monthly_data["month_label"],
        y=-monthly_data["profit"],
        marker_color="#38CE81",
        customdata=monthly_data["profit"],
        hovertemplate="<b>%{x}</b><br>Profit : ₹%{customdata:,.0f}<extra></extra>",
        showlegend=False,
        marker=dict(
            color="#38CE81",
            line=dict(width=0)
        )
    ),
    row=2,
    col=1
    )

    fig.update_xaxes(
    showticklabels=False,
    row=1,
    col=1
    )
    fig.update_xaxes(
    tickmode="array",
    tickvals=monthly_data["month_label"],
    ticktext=monthly_data["month_label"],
    row=2,
    col=1
    )
    fig.update_layout(
    height=650,
    bargap=0.35,

    plot_bgcolor=colors["bg"],
    paper_bgcolor=palette["surface"],

    font=dict(
        color=colors["text"]
    ),

    hovermode="x unified",

    margin=dict(
        l=40,
        r=20,
        t=50,
        b=30
    )
    )

    fig.update_layout(
    yaxis=dict(
        domain=[0.52, 1.0]
    ),

    yaxis2=dict(
        domain=[0.0, 0.48]
    )
    )
    fig.update_yaxes(
    title_text="₹ Revenue",
    title_standoff=25,
    row=1,
    col=1
    )


    fig.update_yaxes(
        title_text="₹ Profit",
        title_standoff=25,
        row=2,
        col=1
    )
    
    fig.update_yaxes(
    range=[-axis_max, 0],
    tickvals=tickvals,
    ticktext=ticktext,
    row=2,
    col=1
    )
    fig.update_xaxes(
    showline=False,
    ticks=""
    )

    fig.update_yaxes(
        showline=False,
        ticks=""
    )
    
    
    fig.update_xaxes(
    showgrid=False
    )
    fig.update_xaxes(gridcolor=colors['grid'])
    fig.update_yaxes(gridcolor=colors['grid'])
    
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error: {str(e)}")

st.caption("Data from last 365 days | Auto-refreshes every 5 minutes")
