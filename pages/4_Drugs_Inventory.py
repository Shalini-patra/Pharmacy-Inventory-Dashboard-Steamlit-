import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.ui_overrides import green_banner, kpi_card
import plotly.graph_objects as go
st.set_page_config(page_title="Drugs Inventory", page_icon="💊", layout="wide")
ThemeManager.init_theme()
ThemeManager.apply_custom_css()

palette = ThemeManager.get_palette()
colors = ColorPalette.get_chart_colors()
status_colors = ColorPalette.get_status_colors()

green_banner("💊 Drugs Inventory")

# ============== SEARCH & FILTER ==============
col1, col2 = st.columns([2, 1])

with col1:
    search_query = st.text_input(
        "🔍 Search by drug name or generic name",
        placeholder="e.g., Amoxicillin, Aspirin..."
    )

with col2:
    show_alternatives = st.checkbox("Show brand alternatives", value=False)

# ============== INVENTORY HEATMAP ==============
try:
    inventory_data = DatabaseManager.get_inventory_data()
    
    search_results = pd.DataFrame()
    if search_query:
        search_results = DatabaseManager.search_inventory_by_generic_or_drug_name(search_query.strip())
        if search_results is None:
            search_results = pd.DataFrame()

    if not search_results.empty:
        st.subheader("Search Results")
        st.dataframe(
            search_results.rename(columns={
                'generic_name': 'Generic Name',
                'drug_id': 'Drug ID',
                'drug_name': 'Drug Name',
                'strength': 'Strength',
                'remaining_stock': 'Remaining Quantity',
                'unit_price_inr': 'Unit Price (₹)',
                'expiry_date': 'Expiry Date',
            }),
            use_container_width=True,
            hide_index=True,
        )
    elif search_query:
        st.info("No matching drugs were found for the entered name or generic name.")

    if len(inventory_data) > 0:
        total_stock = int(inventory_data['remaining_stock'].fillna(0).sum())
        low_stock_count = int((inventory_data['stock_status'].isin(['Yellow', 'Red'])).sum())
        safe_stock_count = int((inventory_data['stock_status'] == 'Safe').sum())

        kpi_cols = st.columns(3, gap='small')
        with kpi_cols[0]:
            kpi_card(
                label="Total Stock",
                value=f"{total_stock:,.0f}",
                tooltip_pairs=[
                    ("What it measures", "Combined remaining stock across all tracked drugs."),
                    ("Why it matters", "Provides a quick view of inventory volume."),
                ],
                icon="📦",
                icon_color="positive",
                subtitle="Current availability",
            )
        with kpi_cols[1]:
            kpi_card(
                label="Low Stock Items",
                value=f"{low_stock_count}",
                tooltip_pairs=[
                    ("What it measures", "Drugs currently marked as Yellow or Red."),
                    ("Why it matters", "Signals inventory risk and the need for attention."),
                ],
                icon="⚠️",
                icon_color="warning",
                subtitle="At-risk inventory",
            )
        with kpi_cols[2]:
            kpi_card(
                label="Safe Stock Items",
                value=f"{safe_stock_count}",
                tooltip_pairs=[
                    ("What it measures", "Drugs currently in the Safe state."),
                    ("Why it matters", "Shows how much inventory is operating within normal thresholds."),
                ],
                icon="✅",
                icon_color="info",
                subtitle="Healthy inventory",
            )

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        # Create heatmap
        
        if len(inventory_data) > 0:

        # ================================================
        # INVENTORY BY THERAPEUTIC CATEGORY
        # ================================================

            st.subheader("Inventory Distribution by Therapeutic Category")

            category_stock = (
                inventory_data.groupby("therapeutic_category", as_index=False)
                .agg(
                    total_stock=("remaining_stock", "sum"),
                    drug_count=("drug_id", "count"),
                )
                .sort_values("total_stock", ascending=True)
            )

            fig = px.bar(
                category_stock,
                x="total_stock",
                y="therapeutic_category",
                orientation="h",
                text="total_stock",
                color="total_stock",
                color_continuous_scale=[
                    "#D7F5E5",
                    "#A9E8C7",
                    "#6ED79F",
                    "#38CE81",
                    "#05A154",
                ],
                hover_data={
                    "drug_count": True,
                    "total_stock": ":,.0f",
                },
            )

            fig.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
            )

            fig.update_layout(
                height=450,
                plot_bgcolor=colors["bg"],
                paper_bgcolor=palette["surface"],
                font=dict(color=colors["text"]),
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Total Remaining Stock",
                yaxis_title="Therapeutic Category",
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            st.subheader("Browse Drugs by Therapeutic Category")

            categories = sorted(
                inventory_data["therapeutic_category"].dropna().unique()
            )

            selected_category = st.selectbox(
                "Select Therapeutic Category",
                ["Select Category"] + categories,
            )
            if selected_category != "Select Category":
                filtered_inventory = inventory_data[
                        inventory_data["therapeutic_category"] == selected_category
                    ].copy()
                
                filtered_inventory = (
                    filtered_inventory
                    .sort_values("remaining_stock")
                )

                fig2 = go.Figure()
                # Normalize remaining stock (High stock = Green, Low stock = Red)

                filtered_inventory["stock_score"] = (
                    filtered_inventory["remaining_stock"]
                    - filtered_inventory["remaining_stock"].min()
                )

                filtered_inventory["stock_score"] = (
                    filtered_inventory["stock_score"]
                    / filtered_inventory["stock_score"].max()
                )
                # Lines
                fig2 = px.treemap(

                    filtered_inventory,

                    path=[
                        "generic_name",
                        "drug_name"
                    ],

                    values="remaining_stock",

                    color="stock_score",

                    color_continuous_scale=[
                        (0.00, "#D7191C"),   # Red
                        (0.25, "#EB6112"),   # Orange
                        (0.50, "#FDE725"),   # Yellow
                        (0.75, "#6CC644"),   # Light Green
                        (1.00, "#07462B")    # Dark Green
                    ],

                    hover_data={
                        "remaining_stock": ":,.0f",
                        "strength": True,
                        "expiry_date": True,
                        "stock_status": True,
                        "abc_class": True,
                    },
                )
                # Dots
                fig2.update_traces(

                    textfont=dict(

                        color="white",

                        size=15,

                        family="Arial Black"
                    ),

                    marker=dict(

                        line=dict(

                            color="#18372A",

                            width=2
                        )
                    ),

                    hovertemplate=
                    "<b>%{label}</b><br><br>"
                    "Remaining Stock : %{value:,.0f}<br>"
                    "Stock Status : %{customdata[3]}<br>"
                    "ABC Class : %{customdata[4]}<extra></extra>"
                )

                fig2.update_layout(

                    title=dict(

                        text=f"{selected_category} Inventory",

                        x=0,

                        font=dict(

                            size=28,

                            color="white"
                        )
                    ),

                    paper_bgcolor="#061B15",

                    plot_bgcolor="#061B15",

                    margin=dict(

                        l=10,

                        r=10,

                        t=50,

                        b=10
                    ),

                    font=dict(

                        color="white",

                        size=15
                    ),

                    coloraxis_showscale=True,

                    coloraxis_colorbar=dict(

                        title="Remaining Stock",

                        orientation="h",

                        x=0.5,

                        y=-0.22,

                        xanchor="center",

                        tickvals=[0,0.5,1],

                        ticktext=["Low","Medium","High"],

                        len=0.5,
                    )
                )
                fig2.update_traces(

                    textinfo="label+value"
                )
                st.plotly_chart(
                    fig2,
                    use_container_width=True,
                )

        # ============== DRUG DETAILS ==============
        if show_alternatives:
            st.subheader("Brand Alternatives")
            
            selected_drug = st.selectbox(
                "Select a drug to view alternatives",
                options=inventory_data['drug_name'].unique()
            )
            
            if selected_drug:
                alternatives = DatabaseManager.get_drug_alternatives(selected_drug)
                
                if not alternatives.empty:
                    st.dataframe(
                        alternatives,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'drug_id': st.column_config.TextColumn('Drug ID', width='small'),
                            'drug_name': st.column_config.TextColumn('Brand Name'),
                            'generic_name': st.column_config.TextColumn('Generic Name'),
                            'strength': st.column_config.TextColumn('Strength'),
                            'unit_price_inr': st.column_config.NumberColumn('Price (₹)', format="₹%.2f"),
                        }
                    )

    # ============== NEW INVENTORY STOCK UPDATE ==============
    st.markdown("---")
    st.subheader("New Inventory Stock Update")

    drug_lookup = DatabaseManager.get_drug_lookup()
    drug_lookup = drug_lookup.drop_duplicates(subset=['drug_id', 'drug_name']).reset_index(drop=True)
    drug_name_map = {row['drug_name']: row['drug_id'] for _, row in drug_lookup.iterrows()}

    with st.form(key='inventory_update_form'):
        col1, col2, col3 = st.columns(3, gap='small')

        with col1:
            snapshot_date = st.date_input(
                'Snapshot Date',
                value=datetime.today(),
                key='snapshot_date'
            )
            # Present drug_id options but display friendly "Drug Name (Drug ID)" labels
            drug_id_options = ['Select a drug'] + drug_lookup['drug_id'].tolist()

            def _format_drug_id(did):
                if did == 'Select a drug':
                    return did
                row = drug_lookup[drug_lookup['drug_id'] == did]
                if not row.empty:
                    return f"{row.iloc[0]['drug_name']} ({did})"
                return str(did)

            selected_drug_id = st.selectbox(
                'Drug Name',
                options=drug_id_options,
                index=0,
                help='Search and select a drug name to update inventory.',
                format_func=_format_drug_id,
            )

            # Show read-only Drug ID field (empty when nothing selected)
            st.text_input('Drug ID', value=selected_drug_id if selected_drug_id != 'Select a drug' else '', disabled=True)

        with col2:
            expiry_date = st.date_input(
                'Expiry Date',
                value=datetime.today(),
                key='expiry_date'
            )
            remaining_stock = st.number_input(
                'Remaining Stock',
                min_value=0,
                step=1,
                value=0,
                format='%d'
            )

        with col3:
            unit_cost_inr = st.number_input(
                'Unit Cost (INR)',
                min_value=0.0,
                step=0.01,
                value=0.0,
                format='%.2f'
            )
            submit_update = st.form_submit_button('Update Inventory')

        if submit_update:
            validation_errors = []
            if not snapshot_date:
                validation_errors.append('Snapshot Date is required.')
            if not selected_drug_id:
                validation_errors.append('Drug Name must be selected.')
            if not expiry_date:
                validation_errors.append('Expiry Date is required.')
            if remaining_stock <= 0:
                validation_errors.append('Remaining Stock must be greater than 0.')
            if unit_cost_inr <= 0:
                validation_errors.append('Unit Cost must be greater than 0.')

            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                snapshot_str = snapshot_date.strftime('%Y%m%d')
                expiry_date_str = expiry_date.strftime('%Y-%m-%d')
                latest_batch = DatabaseManager.get_latest_batch_id_for_drug_and_date(selected_drug_id, snapshot_str)
                suffix = 1
                if latest_batch:
                    try:
                        suffix = int(latest_batch.split('-')[-1]) + 1
                    except ValueError:
                        suffix = 1
                batch_id = f"{selected_drug_id}-{snapshot_str}-{suffix}"
                stock_value_inr = remaining_stock * unit_cost_inr

                try:
                    DatabaseManager.insert_inventory_snapshot(
                        snapshot_date=snapshot_date,
                        drug_id=selected_drug_id,
                        batch_id=batch_id,
                        manufacturing_date=snapshot_date,
                        expiry_date=expiry_date,
                        remaining_stock=remaining_stock,
                        unit_cost_inr=unit_cost_inr,
                        stock_value_inr=stock_value_inr,
                    )
                    DatabaseManager.insert_restock_transaction(
                        transaction_id=f"RST{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        drug_id=selected_drug_id,
                        batch_id=batch_id,
                        transaction_date=snapshot_date,
                        quantity=remaining_stock,
                        unit_cost_inr=unit_cost_inr,
                        unit_price_inr=unit_cost_inr,
                    )
                    st.success(
                        'Inventory updated successfully.\nNew inventory batch and restock transaction have been added and will be fully processed during the next scheduled ETL run.'
                    )
                    st.experimental_rerun()
                except Exception:
                    st.error('❌ Unable to update inventory at this time. Please try again or contact support.')

except Exception as e:
    st.error('❌ Error: unable to load drugs inventory data at this time.')
