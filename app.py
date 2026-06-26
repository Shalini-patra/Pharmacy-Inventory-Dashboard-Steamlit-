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
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("# 🏥 Pharmacy Inventory Dashboard")
    st.markdown("**Real-time monitoring of stock levels, reorders, and financial performance**")

with col2:
    # Last updated timestamp
    st.markdown(f"""
    <div style='text-align: right; color: {palette['text_secondary']}; font-size: 12px;'>
    Updated: {datetime.now().strftime('%H:%M:%S')}<br>
    {datetime.now().strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)

# ============== WELCOME MESSAGE ==============
col1, col2, col3 = st.columns(3)

box_style = """
padding:8px 12px;
border-radius:8px;
font-size:11px;
font-weight:500;
"""

with col1:
    st.markdown(f"""
    <div style="{box_style} background:#d1ecf1; color:#0c5460; border:1px solid #bee5eb;">
        💡 <b>Tip:</b> Use the sidebar to navigate between different pages
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="{box_style} background:#d4edda; color:#155724; border:1px solid #c3e6cb;">
        ✅ <b>Status:</b> All systems operational
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="{box_style} background:#fff3cd; color:#856404; border:1px solid #ffeeba;">
        📊 <b>Data:</b> Updates every 5 minutes
    </div>
    """, unsafe_allow_html=True)

# ============== OVERVIEW CARDS ON HOMEPAGE ==============
st.subheader("🎯 Quick Overview")

try:
    from lib.db import DatabaseManager
    
    # Fetch quick metrics
    monthly_rev = DatabaseManager.get_monthly_revenue_metrics()
    reorder_list = DatabaseManager.get_reorder_list()
    
    col1, col2, col3, col4 = st.columns(4)
    
    if len(monthly_rev) > 0:
        current_rev = monthly_rev.iloc[0]['total_revenue'] or 0
        current_profit = monthly_rev.iloc[0]['total_profit'] or 0
        
        with col1:
            st.metric(
                "💰 This Month Revenue",
                f"₹{current_rev:,.0f}",
                help="Total revenue for current month"
            )
        
        with col2:
            st.metric(
                "📈 This Month Profit",
                f"₹{current_profit:,.0f}",
                help="Net profit after cost of goods"
            )
    
    # Operational (drug-level SUM) triage to keep homepage consistent with Reorder Management.
    try:
        action_rows = DatabaseManager.get_reorder_action_rows()
        num_reorder = int((action_rows['stock_status'] == 'Immediate Reorder Needed').sum()) if action_rows is not None and not action_rows.empty else 0
    except Exception:
        num_reorder = 0
    
    with col3:
        if num_reorder > 0:
            st.metric(
                "🔴 Reorder Needed",
                num_reorder,
                "URGENT - Click Reorder Management page"
            )
        else:
            st.metric(
                "🟢 Reorder Needed",
                0,
                "All drugs in safe stock"
            )

    
    with col4:
        today = datetime.now().date()
        st.metric(
            "📅 Last Updated",
            today.strftime("%d %b %Y"),
            datetime.now().strftime("%H:%M:%S")
        )

except Exception as e:
    st.error(f"⚠️ Error loading metrics: {str(e)}")

st.markdown(
    """
    <hr style="
        margin-top:8px;
        margin-bottom:8px;
        border:0.5px solid #3d3d3d;
    ">
    """,
    unsafe_allow_html=True
)

# ============== STATISTICS SECTION ==============
st.subheader("📈 System Statistics")

col1, col2, col3 = st.columns(3)

try:
    from lib.db import DatabaseManager
    
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    # Total transactions
    cursor.execute("""
        SELECT COUNT(*) FROM transactions 
        WHERE CAST(transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '30 days';
    """)
    transactions_30d = cursor.fetchone()[0] or 0
    
    # Average daily sales
    cursor.execute("""
        SELECT ROUND(COUNT(*)::NUMERIC / 30, 0) 
        FROM transactions 
        WHERE CAST(transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '30 days'
        AND transaction_type = 'Sale';
    """)
    avg_daily_sales = cursor.fetchone()[0] or 0
    
    # Stock health %
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


# ============== MAIN CONTENT AREA ==============
st.markdown("""
### 📍 Getting Started with Your Dashboard

**Select a page from the sidebar menu to explore:**

#### 📊 **Executive Overview**
View key performance indicators, top/bottom performing drugs, revenue trends, and customer insights at a glance.

#### 📦 **Reorder Management**
Monitor drugs that need immediate reorder. View supplier details, suggested quantities, and delivery times. Take action with one-click email alerts.

#### 💰 **Transactions & Revenue**
Analyze monthly revenue, profit trends, and transaction patterns. Identify seasonal variations and growth opportunities.

#### 💊 **Drugs Inventory**
Explore stock levels using interactive heatmaps. Search for drugs, view brand alternatives, and check stock status (Safe/Yellow/Red).

#### 👥 **Customers Analysis**
Analyze regular customers, purchase frequency, spending patterns, and customer lifetime value.

#### 📈 **ABC Analysis**
Understand revenue concentration through ABC classification. Identify high-impact drugs (Class A), medium-impact (Class B), and low-impact (Class C) items.

#### 🔗 **Bundle Analysis**
Discover frequently bought-together drug combinations. Use insights for strategic bundling and cross-selling opportunities.

#### ⚙️ **Settings**
Configure dashboard preferences, admin panel, user settings, and system configuration.

---

### 🎯 Key Features

✅ **Real-time Data** - Connected to NeonDB, updates every 5 minutes  
✅ **Interactive Visualizations** - Plotly charts with hover, zoom, pan  
✅ **Dark/Light Theme** - Toggle theme using sidebar buttons  
✅ **Cross-Filtering** - Click charts to filter related data  
✅ **Responsive Design** - Works on desktop, tablet, mobile  
✅ **Export Capabilities** - Download data as CSV/PDF  
✅ **Alert System** - Notifications for critical stock levels  
✅ **Advanced Analytics** - Churn analysis, bundle analytics, ABC classification

---

### 📊 Data Metrics Tracked

**Inventory Metrics:**
- Stock levels by drug
- Reorder points & safety stock
- Stock status (Safe/Yellow/Red)
- ABC classification (A/B/C)
- Days of stock remaining

**Financial Metrics:**
- Monthly revenue & profit
- Cost analysis per drug
- Loss metrics (stockout + expiry)
- ROI of smart dashboard
- Gross margin %

**Customer Metrics:**
- Transaction frequency
- Spending patterns
- Churn rate
- Regular customer %
- Customer lifetime value

**Operational Metrics:**
- Delivery lead times
- Reorder history
- Bundle/cross-sell patterns
- Seasonal demand
- Forecast accuracy

---

### 💡 Pro Tips

1. **Start with Executive Overview** to understand overall performance
2. **Check Reorder Management daily** to stay on top of inventory
3. **Use dark theme for evening viewing** (easier on eyes)
4. **Export data for meetings** using the CSV export button
5. **Set up email alerts** in Settings for critical reorders

""")

st.markdown(
    """
    <hr style="
        margin-top:8px;
        margin-bottom:8px;
        border:0.5px solid #3d3d3d;
    ">
    """,
    unsafe_allow_html=True
)


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