# app.py
"""
Pharmacy Inventory Dashboard - Main Entry Point

Multi-page Streamlit application with:
- Dark/Light theme toggle
- Sidebar navigation
- Real-time data from NeonDB
- Interactive visualizations
- Cross-filtering capabilities
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============== PAGE CONFIGURATION ==============
st.set_page_config(
    page_title="🏥 Pharmacy Inventory Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Pharmacy Inventory Smart Monitoring Dashboard v1.0 | Powered by Streamlit & NeonDB",
        "Get Help": "mailto:support@pharmacy.com",
    }
)

# ============== INITIALIZE APP ==============
from lib.theme import ThemeManager
from lib.session_state import SessionStateManager
from lib.ui_overrides import kpi_card

ThemeManager.init_theme()
SessionStateManager.init_filters()
ThemeManager.apply_custom_css()

# ============== SIDEBAR ==============
with st.sidebar:
    st.title("🏥 Pharmacy Dashboard")
    st.markdown("---")
    
    st.subheader("⚙️ Settings")
    st.markdown("---")

    
    # Get current palette
    palette = ThemeManager.get_palette()
    
    # App info
    st.subheader("📊 Dashboard Info")
    
    try:
        from lib.db import DatabaseManager
        conn_status = DatabaseManager.test_connection()
        status_text = "✅ Connected" if conn_status else "❌ Disconnected"
        status_color = "green" if conn_status else "red"
    except:
        status_text = "❌ Error"
        status_color = "red"
    
    st.info(
        f"""
        **Status:** {status_text}
        
        **Last Sync:** {datetime.now().strftime('%H:%M:%S')}
        
        **Theme:** Dark

        
        **Data Source:** NeonDB (PostgreSQL)
        
        **Version:** 1.0.0
        """
    )
    
    st.markdown("---")
    
    # Navigation info
    st.subheader("📑 Dashboard Pages")
    st.markdown("""
    1. **📊 Executive Overview**
       KPIs, top/bottom drugs, revenue, profit trend
    
    2. **📦 Reorder Management**
       Drugs needing reorder with supplier details
    
    3. **💰 Transactions & Revenue**
       Monthly revenue & profit analysis
    
    4. **💊 Drugs Inventory**
       Stock heatmap, search, brand alternatives
    
    5. **👥 Customers Analysis**
       Regular customers, purchase patterns
    
    6. **📈 ABC Analysis**
       Revenue classification, metrics
    
    7. **🔗 Bundle Analysis**
       Frequently bought together
    
    8. **⚙️ Settings**
       Configuration & admin panel
    """)
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("⚡ Quick Stats")
    
    try:
        from lib.db import DatabaseManager
        
        # Fetch quick metrics
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # Total drugs
        cursor.execute("SELECT COUNT(*) FROM drugs;")
        num_drugs = cursor.fetchone()[0]
        
        # Total customers
        cursor.execute("SELECT COUNT(DISTINCT customer_id) FROM  transactions;")
        num_customers = cursor.fetchone()[0]
        
        # Drugs needing reorder (consistent operational logic)
        # Count rows grouped as "Immediate Reorder Needed" from the triage calculation.
        # Uses reorder_points vs remaining_stock, not inventory_snapshots.stock_status.
        from lib.db import DatabaseManager
        action_rows = DatabaseManager.get_reorder_action_rows()
        num_reorder = int((action_rows['stock_status'] == 'Immediate Reorder Needed').sum()) if action_rows is not None and not action_rows.empty else 0

        
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("💊 Total Drugs", num_drugs)
            st.metric("👥 Customers", num_customers)
        
        with col2:
            st.metric("🔴 Reorder Now", num_reorder)
            if num_reorder > 0:
                st.warning(f"⚠️ {num_reorder} drug(s) need immediate reorder!")
        
    except Exception as e:
        st.warning(f"⚠️ Could not load stats: {str(e)[:50]}")
    
    st.markdown("---")
    
    # Footer
    st.caption("""
    **🏥 Pharmacy Inventory Monitoring**
    
    v1.0.0 | © 2024 All Rights Reserved
    
    Built with ❤️ using Streamlit & PostgreSQL
    """)

# ============== MAIN CONTENT ==============
palette = ThemeManager.get_palette()

with st.container():
    st.markdown("<div class='dashboard-shell'>", unsafe_allow_html=True)

    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown("<div class='dashboard-title-block'>", unsafe_allow_html=True)
        st.markdown("# 🏥 Pharmacy Inventory Dashboard")
        st.markdown("**Real-time monitoring of stock levels, reorders, and financial performance**")
        st.markdown("</div>", unsafe_allow_html=True)

    with header_col2:
        st.markdown(f"""
        <div class='dashboard-timestamp'>
        Updated: {datetime.now().strftime('%H:%M:%S')}<br>
        {datetime.now().strftime('%Y-%m-%d')}
        </div>
        """, unsafe_allow_html=True)

    chip_col1, chip_col2, chip_col3 = st.columns(3)
    with chip_col1:
        st.markdown("<div class='dashboard-chip'>💡 Use the sidebar to move between dashboards quickly</div>", unsafe_allow_html=True)
    with chip_col2:
        st.markdown("<div class='dashboard-chip'>✅ All systems operational and synced</div>", unsafe_allow_html=True)
    with chip_col3:
        st.markdown("<div class='dashboard-chip'>📊 Data refreshes every 5 minutes</div>", unsafe_allow_html=True)

    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.markdown("### 🎯 Quick Overview")
    try:
        from lib.db import DatabaseManager

        monthly_rev = DatabaseManager.get_monthly_revenue_metrics()
        col1, col2, col3, col4 = st.columns(4)

        if len(monthly_rev) > 0:
            current_rev = monthly_rev.iloc[0]['total_revenue'] or 0
            current_profit = monthly_rev.iloc[0]['total_profit'] or 0

            with col1:
                kpi_card(
                    label="This Month Revenue",
                    value=f"₹{current_rev:,.0f}",
                    tooltip_pairs=[
                        ("What it measures", "Total revenue captured for the current month."),
                        ("Why it matters", "Shows current business income performance."),
                    ],
                    delta="Current month",
                    icon="💰",
                    icon_color="positive",
                    subtitle="Income generated",
                )

            with col2:
                kpi_card(
                    label="This Month Profit",
                    value=f"₹{current_profit:,.0f}",
                    tooltip_pairs=[
                        ("What it measures", "Net profit after cost of goods for the current month."),
                        ("Why it matters", "Shows current profitability and operating efficiency."),
                    ],
                    delta="Current month",
                    icon="₹",
                    icon_color="info",
                    subtitle="Net profitability",
                )

        try:
            action_rows = DatabaseManager.get_reorder_action_rows()
            if action_rows is not None and not action_rows.empty and 'stock_status' in action_rows.columns:
                num_reorder = int((action_rows['stock_status'] == 'Immediate Reorder Needed').sum())
            else:
                num_reorder = 0
        except Exception:
            num_reorder = 0

        with col3:
            if num_reorder > 0:
                kpi_card(
                    label="Reorder Needed",
                    value=f"{num_reorder}",
                    tooltip_pairs=[
                        ("What it measures", "Number of drugs still requiring immediate reorder."),
                        ("Why it matters", "Highlights urgent replenishment needs."),
                    ],
                    delta="Urgent action",
                    icon="🔴",
                    icon_color="danger",
                    subtitle="Immediate follow-up",
                )
            else:
                kpi_card(
                    label="Reorder Needed",
                    value="0",
                    tooltip_pairs=[
                        ("What it measures", "Number of drugs currently needing reorder."),
                        ("Why it matters", "Confirms inventory is in safe stock."),
                    ],
                    delta="All clear",
                    icon="🟢",
                    icon_color="positive",
                    subtitle="Healthy inventory",
                )

        with col4:
            today = datetime.now().date()
            kpi_card(
                label="Last Updated",
                value=today.strftime("%d %b %Y"),
                tooltip_pairs=[
                    ("What it measures", "The latest dashboard refresh timestamp."),
                    ("Why it matters", "Shows how current the displayed data is."),
                ],
                delta=datetime.now().strftime("%H:%M:%S"),
                icon="📅",
                icon_color="warning",
                subtitle="Freshness of data",
            )

    except Exception as e:
        st.error(f"⚠️ Error loading metrics: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.markdown("### 📈 System Statistics")
    col1, col2, col3 = st.columns(3)
    try:
        from lib.db import DatabaseManager

        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE CAST(transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '30 days';
        """)
        transactions_30d = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT ROUND(COUNT(*)::NUMERIC / 30, 0) 
            FROM transactions 
            WHERE CAST(transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '30 days'
            AND transaction_type = 'Sale';
        """)
        avg_daily_sales = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT 
                ROUND(
                    COUNT(CASE WHEN stock_status = 'Safe' THEN 1 END)::NUMERIC / 
                    NULLIF(COUNT(*),0)::NUMERIC * 100, 
                    1
                )
            FROM inventory_snapshots 
            WHERE snapshot_date = CURRENT_DATE;
        """)
        stock_health = cursor.fetchone()[0] or 0

        conn.close()

        with col1:
            st.metric("📊 Transactions (30d)", f"{int(transactions_30d):,}")

        with col2:
            st.metric("💳 Avg Daily Sales", f"{int(avg_daily_sales)} txns")

        with col3:
            st.metric("🟢 Stock Health", f"{stock_health:.1f}%", "Safe stock")

    except Exception as e:
        st.warning(f"Could not load statistics: {str(e)[:40]}")
    st.markdown("</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.15, 1], gap="small")

    with left_col:
        st.markdown("<div class='dashboard-card compact-section'>", unsafe_allow_html=True)
        st.markdown("### 📍 Getting Started")
        st.markdown("**Select a page from the sidebar to explore the dashboard.**")
        st.markdown("- 📊 Executive Overview for KPIs and trends")
        st.markdown("- 📦 Reorder Management for urgent stock actions")
        st.markdown("- 💰 Transactions & Revenue for financial insights")
        st.markdown("- 💊 Drugs Inventory for stock and alternatives")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='dashboard-card compact-section'>", unsafe_allow_html=True)
        st.markdown("### 🎯 Key Features")
        st.markdown("- Real-time data from NeonDB")
        st.markdown("- Interactive Plotly visualizations")
        st.markdown("- Responsive design for desktop and tablet")
        st.markdown("- Alerting for critical stock levels")
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("<div class='dashboard-card compact-section'>", unsafe_allow_html=True)
        st.markdown("### 📊 Metrics Tracked")
        st.markdown("**Inventory**")
        st.markdown("- Stock levels and reorder points")
        st.markdown("- Safe / Yellow / Red status")
        st.markdown("- ABC classification and days of stock")
        st.markdown("**Financial**")
        st.markdown("- Monthly revenue and profit")
        st.markdown("- Loss metrics and gross margin")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='dashboard-card compact-section'>", unsafe_allow_html=True)
        st.markdown("### 💡 Pro Tips")
        st.markdown("1. Start with Executive Overview for the full picture")
        st.markdown("2. Check Reorder Management daily for urgent actions")
        st.markdown("3. Use the theme palette for clearer evening viewing")
        st.markdown("4. Export data for meetings when needed")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ============== FOOTER ==============

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption(f"🕐 **Time:** {datetime.now().strftime('%H:%M:%S IST')}")

with footer_col2:
    st.caption(f"📅 **Date:** {datetime.now().strftime('%A, %B %d, %Y')}")

with footer_col3:
    st.caption("**Made with ❤️ using Streamlit + PostgreSQL**")

# ============== HIDDEN DEBUG INFO (DEV ONLY) ==============
if st.session_state.get('debug_mode', False):
    st.divider()
    st.subheader("🔧 Debug Info (Developer Only)")
    
    with st.expander("Session State"):
        st.write(st.session_state)
    
    with st.expander("Theme Settings"):
        palette = ThemeManager.get_palette()
        st.write(f"Current Theme: {st.session_state.get('theme_mode', 'dark')}")
        st.write(f"Palette Keys: {list(palette.keys())}")
    
    with st.expander("Database Connection"):
        try:
            from lib.db import DatabaseManager
            conn_status = DatabaseManager.test_connection()
            st.write(f"Database Connected: {conn_status}")
        except Exception as e:
            st.error(f"Error: {str(e)}")