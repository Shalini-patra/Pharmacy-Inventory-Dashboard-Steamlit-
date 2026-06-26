"""
Bundle Analysis Page - Frequently Bought Together

Shows which drugs are commonly purchased together.
Uses market basket analysis to identify bundling opportunities.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.ui_overrides import green_banner, kpi_card
from lib.session_state import SessionStateManager
from lib.calculations import AdvancedCalculations

# ============== PAGE CONFIG ==============
st.set_page_config(
    page_title="Bundle Analysis",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== INITIALIZE ==============
ThemeManager.init_theme()
ThemeManager.apply_custom_css()
SessionStateManager.init_filters()


palette = ThemeManager.get_palette()
colors = ColorPalette.get_chart_colors()

# ============== PAGE HEADER ==============
green_banner("🔗 Bundle Analysis - Frequently Bought Together")
st.markdown("""
**Discover which drugs are frequently purchased together.**

Use these insights for:
- 💡 **Strategic Bundling** - Create attractive bundle offers
- 📦 **Cross-Selling** - Recommend complementary products
- 📊 **Inventory Planning** - Stock related items together
- 💰 **Revenue Growth** - Increase average transaction value
""")

st.divider()

# ============== BUNDLE INSIGHTS ==============
st.subheader("🎯 Bundle Insights")

try:
    # Get frequently bought together data
    bundle_data = AdvancedCalculations.calculate_frequently_bought_together(min_support=0.02)
    
    if len(bundle_data) > 0:
        # ============== TOP BUNDLES TABLE ==============
        st.subheader("📊 Top Drug Pairs (Frequently Bought Together)")
        
        # Format display table
        display_bundles = bundle_data.copy()
        display_bundles.columns = [
            'Drug 1 ID', 'Drug 2 ID', 'Drug 1 Name', 'Drug 2 Name',
            'Co-Occurrences', 'Support %'
        ]
        
        # Remove IDs from display, keep only names
        display_bundles = display_bundles[[
            'Drug 1 Name', 'Drug 2 Name', 'Co-Occurrences', 'Support %'
        ]]
        
        # Create styled dataframe
        st.dataframe(
            display_bundles,
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                'Drug 1 Name': st.column_config.TextColumn('First Drug', width='medium'),
                'Drug 2 Name': st.column_config.TextColumn('Second Drug', width='medium'),
                'Co-Occurrences': st.column_config.NumberColumn('Times Bought Together', format='%d'),
                'Support %': st.column_config.NumberColumn('Frequency %', format='%.2f%%'),
            }
        )
        
        st.caption(f"Data from last 90 days | Found {len(bundle_data)} frequently bought pairs")
        
        # ============== BUNDLE VISUALIZATION ==============
        st.subheader("📈 Bundle Frequency Distribution")
        
        # Create bar chart for top bundles
        top_bundles = bundle_data.head(10).copy()
        top_bundles['bundle_name'] = (
            top_bundles['drug_1_name'].str[:15] + ' + ' + 
            top_bundles['drug_2_name'].str[:15]
        )
        
        fig_bar = px.bar(
            top_bundles,
            x='support_pct',
            y='bundle_name',
            orientation='h',
            title='Top 10 Drug Bundles by Frequency',
            labels={
                'support_pct': 'Frequency (%)',
                'bundle_name': 'Drug Bundle',
                'co_occurrence_count': 'Times Bought'
            },
            hover_data=['co_occurrence_count'],
            color='support_pct',
            color_continuous_scale='Viridis'
        )
        
        fig_bar.update_layout(
            height=400,
            plot_bgcolor=colors['bg'],
            paper_bgcolor=palette['surface'],
            font=dict(color=colors['text']),
            xaxis_title='Support % (Frequency of Co-Purchase)',
            yaxis_title='',
            showlegend=False,
            hovermode='closest',
        )
        
        fig_bar.update_xaxes(gridcolor=colors['grid'])
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # ============== BUNDLE STRENGTH ANALYSIS ==============
        st.subheader("💪 Bundle Strength Analysis")
        
        col1, col2, col3 = st.columns(3, gap="small")
        
        with col1:
            strongest_bundle = bundle_data.iloc[0]
            kpi_card(
                label="Strongest Bundle",
                value=f"{strongest_bundle['drug_1_name'][:20]} +<br>{strongest_bundle['drug_2_name'][:20]}",
                tooltip_pairs=[
                    ("What it measures", "The top drug pair by co-purchase support percentage."),
                    ("Why it matters", "Reveals the most valuable bundle opportunity for promotions."),
                ],
                delta=f"{strongest_bundle['support_pct']:.2f}% support",
            )
        
        with col2:
            avg_support = bundle_data['support_pct'].mean()
            kpi_card(
                label="Average Support",
                value=f"{avg_support:.2f}%",
                tooltip_pairs=[
                    ("What it measures", "Mean support across all bundle pairs."),
                    ("Why it matters", "Indicates overall bundle purchase strength."),
                ],
                delta=f"across {len(bundle_data)} pairs",
            )
        
        with col3:
            strong_pairs = len(bundle_data[bundle_data['support_pct'] > 5])
            kpi_card(
                label="Strong Pairs",
                value=f"{strong_pairs}",
                tooltip_pairs=[
                    ("What it measures", "Count of bundle pairs with strong co-purchase support."),
                    ("Why it matters", "Highlights pairs worth promoting together."),
                ],
                delta="(>5% support)",
            )
        
        st.divider()
        
        # ============== DETAILED BUNDLE ANALYSIS ==============
        st.subheader("🔍 Detailed Bundle Breakdown")
        
        # Select a bundle to analyze
        bundle_options = [
            f"{row['drug_1_name']} + {row['drug_2_name']}" 
            for _, row in bundle_data.head(15).iterrows()
        ]
        
        selected_bundle = st.selectbox(
            "Select a bundle to analyze",
            options=["Select a bundle to analyze"] + bundle_options,
            index=0,
            key='bundle_select'
        )
        
        if selected_bundle and selected_bundle != "Select a bundle to analyze":
            # Find the selected bundle
            bundle_parts = selected_bundle.split(' + ')
            drug1_name = bundle_parts[0]
            drug2_name = bundle_parts[1]
            
            selected_bundle_row = bundle_data[
                (bundle_data['drug_1_name'] == drug1_name) & 
                (bundle_data['drug_2_name'] == drug2_name)
            ].iloc[0]
            
            # Display bundle details
            col1, col2, col3, col4 = st.columns(4, gap="small")
            
            with col1:
                kpi_card(
                    label="First Drug",
                    value=drug1_name,
                    tooltip_pairs=[
                        ("What it measures", "Primary drug in the selected bundle."),
                        ("Why it matters", "Helps identify the anchor product in the pair."),
                    ],
                )
            
            with col2:
                kpi_card(
                    label="Second Drug",
                    value=drug2_name,
                    tooltip_pairs=[
                        ("What it measures", "Complementary drug in the selected bundle."),
                        ("Why it matters", "Shows the paired product recommended together."),
                    ],
                )
            
            with col3:
                kpi_card(
                    label="Co-Purchases",
                    value=f"{int(selected_bundle_row['co_occurrence_count'])}",
                    tooltip_pairs=[
                        ("What it measures", "Number of times this bundle was purchased together."),
                        ("Why it matters", "Reflects the bundle's real market traction."),
                    ],
                    delta="times (90 days)",
                )
            
            with col4:
                kpi_card(
                    label="Support %",
                    value=f"{selected_bundle_row['support_pct']:.2f}%",
                    tooltip_pairs=[
                        ("What it measures", "Share of transactions containing this bundle."),
                        ("Why it matters", "Indicates how common this pair is in customer purchases."),
                    ],
                    delta="of all transactions",
                )
            
            # ============== BUNDLE RECOMMENDATION ==============
            st.subheader("💡 Bundle Recommendation")
            
            co_count = int(selected_bundle_row['co_occurrence_count'])
            support_pct = selected_bundle_row['support_pct']
            
            if support_pct >= 5:
                strength = "🔴 **STRONG**"
                action = "✅ **HIGHLY RECOMMENDED** - Create an official bundle offer"
                strategy = """
                - Offer 5-10% discount when purchased together
                - Cross-display in pharmacy
                - Feature in newsletters/ads
                - Train staff to recommend together
                """
            elif support_pct >= 2:
                strength = "🟡 **MODERATE**"
                action = "✅ **RECOMMENDED** - Consider promoting as a bundle"
                strategy = """
                - Add to recommendation list
                - Display near each other in inventory
                - Mention in customer communications
                - Monitor customer feedback
                """
            else:
                strength = "🟢 **WEAK**"
                action = "⏸️ **NOT RECOMMENDED** - Not yet strong enough for bundling"
                strategy = """
                - Track this pair over time
                - Revisit in 1-2 months
                - Consider other factors (seasonality, complementarity)
                """
            
            st.write(f"**Bundle Strength:** {strength}")
            st.write(f"**Recommendation:** {action}")
            st.write(f"**Strategy:**\n{strategy}")
            
            # ============== PROFITABILITY CALCULATION ==============
            st.subheader("💰 Profitability Estimate")
            
            try:
                conn = DatabaseManager.get_connection()
                
                # Get pricing info for both drugs
                query = f"""
                SELECT 
                    drug_id,
                    drug_name,
                    unit_price_inr,
                    unit_cost_inr,
                    ROUND(((unit_price_inr - unit_cost_inr) / unit_price_inr * 100)::numeric, 1) as margin_pct
                FROM drugs
                WHERE drug_name IN ('{drug1_name}', '{drug2_name}')
                LIMIT 2;
                """
                
                pricing_data = pd.read_sql(query, conn)
                conn.close()
                
                if len(pricing_data) > 0:
                    total_bundle_price = pricing_data['unit_price_inr'].sum()
                    total_bundle_cost = pricing_data['unit_cost_inr'].sum()
                    bundle_margin = total_bundle_price - total_bundle_cost
                    margin_pct = (bundle_margin / total_bundle_price * 100)
                    
                    col1, col2, col3 = st.columns(3, gap="small")
                    
                    with col1:
                        kpi_card(
                            label="Bundle Price",
                            value=f"₹{total_bundle_price:.2f}",
                            tooltip_pairs=[
                                ("What it measures", "Total retail price of the selected bundle."),
                                ("Why it matters", "Shows expected customer spend for this bundle."),
                            ],
                            delta="Combined retail price",
                        )
                    
                    with col2:
                        kpi_card(
                            label="Bundle Cost",
                            value=f"₹{total_bundle_cost:.2f}",
                            tooltip_pairs=[
                                ("What it measures", "Total cost price of the selected bundle."),
                                ("Why it matters", "Supports margin and profitability assessment."),
                            ],
                            delta="Combined cost price",
                        )
                    
                    with col3:
                        kpi_card(
                            label="Bundle Margin",
                            value=f"₹{bundle_margin:.2f}",
                            tooltip_pairs=[
                                ("What it measures", "Profit margin for the selected bundle."),
                                ("Why it matters", "Helps assess bundle profitability."),
                            ],
                            delta=f"{margin_pct:.1f}% margin",
                        )
                    
                    # Revenue impact
                    monthly_potential = co_count * bundle_margin
                    st.info(f"""
                    **Revenue Impact (If Promoted as Bundle):**
                    
                    - **Current co-purchases (90 days):** {co_count} times
                    - **Estimated monthly:** {int(co_count/3)} times
                    - **Monthly revenue potential:** ₹{monthly_potential/3:,.0f}
                    - **Yearly potential:** ₹{monthly_potential * 4:,.0f}
                    """)
            
            except Exception as e:
                st.warning(f"Could not calculate profitability: {str(e)}")
        
        # ============== BUNDLING STRATEGY ==============
        st.divider()
        st.subheader("📋 Bundling Strategy Guide")
        
        st.markdown("""
        ### How to Use This Data
        
        **Step 1: Identify Strong Pairs**
        - Look for pairs with >5% support
        - These are natural complementary products
        
        **Step 2: Verify Complementarity**
        - Are they used together? (e.g., antibiotic + antacid)
        - Do they serve the same patient? (e.g., pain reliever + cold medicine)
        
        **Step 3: Create Bundle Offers**
        - Price the bundle at 5-10% discount
        - Promote together in marketing
        - Display side-by-side in store
        
        **Step 4: Monitor Results**
        - Track bundle sales separately
        - Measure uptake rate
        - Gather customer feedback
        
        **Step 5: Optimize**
        - Adjust pricing based on demand
        - Rotate featured bundles monthly
        - Promote seasonal bundles (e.g., cold medicine + cough syrup in winter)
        
        ---
        
        ### Example Bundles That Work Well
        
        **Medical Bundles:**
        - Antibiotic + Antacid (stomach upset from antibiotics)
        - Pain Reliever + Anti-inflammatory
        - Cough Medicine + Throat Lozenge
        - Blood Pressure Med + Potassium supplement
        
        **Seasonal Bundles:**
        - Winter: Antibiotic + Antihistamine + Vitamin C
        - Summer: Electrolyte + Anti-diarrheal
        - Monsoon: Antibiotic + Antifungal
        
        **Target Audience:**
        - Elderly: Heart meds + Blood pressure monitor supplies
        - Diabetics: Insulin + Glucose strips
        - Allergic: Antihistamine + Decongestant
        """)
    
    else:
        st.warning("⚠️ No frequently bought pairs found yet. More data needed for analysis.")
        st.info("""
        Bundle analysis requires at least 60-90 days of transaction history.
        Once sufficient data is available, frequently bought pairs will appear here.
        """)

except Exception as e:
    st.error(f"❌ Error loading bundle analysis: {str(e)}")
    st.info("Try refreshing the page or check database connection.")

# ============== FOOTER ==============
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data from last 90 days")