import streamlit as st
import pandas as pd
from datetime import datetime
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.ui_overrides import green_banner, kpi_card

st.set_page_config(page_title="Customers Analysis", page_icon="👥", layout="wide")
ThemeManager.init_theme()
ThemeManager.apply_custom_css()

palette = ThemeManager.get_palette()
colors = ColorPalette.get_chart_colors()

green_banner("👥 Customers Analysis")

# ---------------------------
# Sidebar filters
# ---------------------------
with st.sidebar:
    st.subheader("🔎 Filters")
    st.caption("Applies to Customer Analysis KPIs, tables, and lookup")

    try:
        customer_names = DatabaseManager.get_distinct_customer_names()
    except Exception:
        customer_names = []

    selected_customers = st.multiselect(
        "Customer Filter",
        options=customer_names,
        default=[],
        help="Select one or more customers to filter the views. Leave blank to include all customers.",
    )

    apply_date_range = st.checkbox(
        "Enable date range",
        value=False,
        key="ca_apply_date_range",
    )

    start_date = None
    end_date = None
    if apply_date_range:
        start_date = st.date_input(
            "Start Date",
            value=datetime.today().replace(day=1),
            key="ca_start_date",
        )
        end_date = st.date_input(
            "End Date",
            value=datetime.today(),
            key="ca_end_date",
        )

        if start_date is not None and end_date is not None and end_date < start_date:
            st.sidebar.error("End Date cannot be earlier than Start Date")

# Normalize filters
customer_names_filter = selected_customers if selected_customers else None

try:
    regular_customers = DatabaseManager.get_regular_customers(
        min_transactions=5,
        days=90,
        customer_names=customer_names_filter,
        start_date=start_date,
        end_date=end_date,
    )
except Exception as e:
    st.error(f"❌ Error loading customer metrics: {str(e)}")
    regular_customers = pd.DataFrame()

# ============== REGULAR CUSTOMERS ==============
if not regular_customers.empty:
    st.subheader(f"⭐ Regular Customers ({len(regular_customers)} total)")

    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        kpi_card(
            label="Avg Transactions",
            value=f"{regular_customers['num_transactions'].mean():.1f}",
            tooltip_pairs=[
                ("What it measures", "Average number of transactions per regular customer over the last 90 days."),
                ("Why it matters", "Shows customer purchase frequency and loyalty."),
            ],
            icon="🧾",
            icon_color="info",
            subtitle="Purchase frequency",
        )
    with col2:
        kpi_card(
            label="Avg Spending",
            value=f"₹{regular_customers['total_spent'].mean():,.0f}",
            tooltip_pairs=[
                ("What it measures", "Average spending per regular customer."),
                ("Why it matters", "Helps identify high-value customers and revenue trends."),
            ],
            icon="💳",
            icon_color="positive",
            subtitle="Average value per customer",
        )
    with col3:
        kpi_card(
            label="Unique Drugs Purchased",
            value=f"{regular_customers['unique_drugs'].mean():.1f}",
            tooltip_pairs=[
                ("What it measures", "Average distinct drugs purchased per regular customer."),
                ("Why it matters", "Shows breadth of product engagement among customers."),
            ],
            icon="💊",
            icon_color="warning",
            subtitle="Product breadth",
        )

    st.divider()

    # ---------------------------
    # Customer transaction lookup
    # ---------------------------
    st.subheader("Customer Transaction Lookup")
    transaction_lookup_label = "Select Customer"
    customer_lookup_options = ["Select a customer"] + customer_names
    selected_customer = st.selectbox(
        transaction_lookup_label,
        options=customer_lookup_options,
        index=0,
        help="Search and select a customer to view their transaction history.",
        key="ca_selected_customer",
    )

    if selected_customer != "Select a customer":
        try:
            customer_transactions = DatabaseManager.get_customer_transactions(
                customer_name=selected_customer,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            customer_transactions = pd.DataFrame()
            st.error(f"❌ Error loading customer transactions: {str(e)}")

        if not customer_transactions.empty:
            st.markdown(f"#### Transaction history for **{selected_customer}**")
            display_columns = [
                'transaction_date',
                'transaction_id',
                'drug_name',
                'drug_id',
                'quantity',
                'unit_price_inr',
                'total_value_inr',
                'profit',
                'unit_cost',
                'notes',
            ]
            table_df = customer_transactions.copy()
            table_df = table_df[display_columns]
            table_df = table_df.rename(columns={
                'transaction_date': 'Transaction Date',
                'transaction_id': 'Transaction ID',
                'drug_name': 'Drug Name',
                'drug_id': 'Drug ID',
                'quantity': 'Quantity',
                'unit_price_inr': 'Unit Price (₹)',
                'total_value_inr': 'Revenue (₹)',
                'profit': 'Profit (₹)',
                'unit_cost': 'Unit Cost (₹)',
                'notes': 'Notes',
            })
            st.dataframe(table_df, use_container_width=True, hide_index=True)
        else:
            st.info("No transactions found for the selected customer and date range.")

    st.divider()

    # Existing regular customers table
    st.dataframe(
        regular_customers[[
            'customer_name', 'num_transactions', 'unique_drugs',
            'total_spent', 'avg_transaction', 'last_purchase_date'
        ]].rename(columns={
            'customer_name': 'Customer',
            'num_transactions': 'Transactions',
            'unique_drugs': 'Drugs Bought',
            'total_spent': 'Total Spent (₹)',
            'avg_transaction': 'Avg/Transaction (₹)',
            'last_purchase_date': 'Last Purchase',
        }),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No regular customer data available for the selected filters.")
