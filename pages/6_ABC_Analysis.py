import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.ui_overrides import green_banner, kpi_card

st.set_page_config(page_title="ABC Analysis", page_icon="📈", layout="wide")
ThemeManager.init_theme()
ThemeManager.apply_custom_css()


palette = ThemeManager.get_palette()
colors = ColorPalette.get_chart_colors()
abc_colors = ColorPalette.get_abc_colors()

# Helper function for safe integer conversion
def safe_int(val, default=0):
    """Safely convert value to integer, handling NaN and other errors."""
    try:
        if pd.isna(val):
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

green_banner("📈 ABC Classification Analysis")

# ============== ABC INFORMATION ==============
st.markdown("""
### Understanding ABC Classification

**Category A Drugs** 🔴 (High Impact)
- Represent **top 20% of total revenue**
- Small group of **business-critical items**
- **Direct impact** on revenue and patient care
- Require **intensive monitoring and control**
- High priority for stock availability

**Category B Drugs** 🟡 (Medium Impact)
- Represent **next 30-50% of revenue**
- Moderate share of business value
- Require **balanced monitoring** to avoid:
  - Overstocking → expiry losses
  - Shortages → patient care delays
- Standard management practices apply

**Category C Drugs** 🟢 (Low Impact)
- Represent **remaining low-value items**
- Large number of drugs, **small individual revenue**
- Contribute to **inventory complexity**
- Require **simplified management** strategies
- Can use standard reorder points

""")

# ============== ABC METRICS ==============
try:
    abc_data = DatabaseManager.get_abc_analysis()
    
    if len(abc_data) > 0:
        st.subheader("ABC Classification Metrics")
        
        # Create metrics display
        for _, row in abc_data.iterrows():
            col1, col2, col3, col4, col5 = st.columns(5, gap="small")
            
            with col1:
                kpi_card(
                    label=f"Class {row['abc_class']}",
                    value=f"{safe_int(row['num_drugs'])} drugs",
                    tooltip_pairs=[
                        ("What it measures", "Number of drugs in this ABC classification."),
                        ("Why it matters", "Helps prioritize inventory control based on revenue impact."),
                    ],
                )
            
            with col2:
                kpi_card(
                    label="Revenue Share",
                    value=f"{row['revenue_pct']:.1f}%",
                    tooltip_pairs=[
                        ("What it measures", "Revenue percentage contributed by this ABC category."),
                        ("Why it matters", "Shows dependency on high-value product groups."),
                    ],
                )
            
            with col3:
                kpi_card(
                    label="Avg Shelf Life",
                    value=f"{safe_int(row['avg_shelf_life'])} days",
                    tooltip_pairs=[
                        ("What it measures", "Average remaining shelf life for drugs in this category."),
                        ("Why it matters", "Supports expiry risk management and replenishment planning."),
                    ],
                )
            
            with col4:
                kpi_card(
                    label="Needing Reorder",
                    value=f"{safe_int(row['drugs_needing_reorder'])}",
                    tooltip_pairs=[
                        ("What it measures", "Number of drugs in this category currently needing reorder."),
                        ("Why it matters", "Highlights inventory risk for critical items."),
                    ],
                )
            
            with col5:
                st.empty()
            
            st.divider()

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
