import streamlit as st
from datetime import datetime
from lib.db import DatabaseManager


def _normalize_multiselect_options(options: list[str]) -> list[str]:
    return options if options is not None else []


def build_sidebar_filters() -> dict:
    """Creates Power BI-style filters in the sidebar and returns selected values."""

    st.sidebar.markdown(
        "<div style='background:#2AA666; color:#FFFFFF; padding:12px; border-radius:8px; margin-bottom:16px; font-weight:700;'>🔎 Executive Overview Filters</div>",
        unsafe_allow_html=True,
    )

    try:
        drug_names = DatabaseManager.get_distinct_drug_names()
    except Exception:
        drug_names = []

    try:
        therapeutic_categories = DatabaseManager.get_distinct_therapeutic_categories()
    except Exception:
        therapeutic_categories = []

    try:
        customers_dict = DatabaseManager.get_distinct_customers_with_ids()
        if not customers_dict:
            st.sidebar.warning("⚠️ No customers available. Check database connection.")
            customers_dict = {}
    except Exception as e:
        st.sidebar.error(f"❌ Error loading customers: {str(e)}")
        customers_dict = {}

    try:
        years = DatabaseManager.get_distinct_years()
    except Exception:
        years = []

    # --- Drug Name ---
    selected_drug_names = st.sidebar.multiselect(
        "Drug Name",
        options=_normalize_multiselect_options(drug_names),
        default=[],
        key="eo_drug_names",
        help="Select one or more drugs to filter the report. Leave blank to include all drugs.",
    )

    # --- Therapeutic Category ---
    selected_therapeutic_categories = st.sidebar.multiselect(
        "Therapeutic Category",
        options=_normalize_multiselect_options(therapeutic_categories),
        default=[],
        key="eo_therapeutic_categories",
        help="Select one or more therapeutic categories to filter the report. Leave blank to include all categories.",
    )

    # --- Customer (Name + ID) ---
    selected_customer_labels = st.sidebar.multiselect(
        "Customer (Name + ID)",
        options=list(customers_dict.keys()) if customers_dict else [],
        default=[],
        key="eo_customer_ids",
        help="Select one or more customers to filter the report. Leave blank to include all customers.",
    )
    selected_customer_ids = [customers_dict[label] for label in selected_customer_labels if label in customers_dict]

    # --- Year ---
    year_options = ["Select Year"] + [str(y) for y in years]
    selected_year = st.sidebar.selectbox(
        "Year",
        options=year_options,
        index=0,
        key="eo_year",
        help="Leave blank to include all years.",
    )

    # --- Month ---
    month_options = ["Select Month", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    selected_month = st.sidebar.selectbox(
        "Month",
        options=month_options,
        index=0,
        key="eo_month",
        help="Leave blank to include all months.",
    )

    st.sidebar.markdown("<div style='color:#FFFFFF; margin-top:12px; margin-bottom:6px;'>Date range is optional. Enable to filter the view.</div>", unsafe_allow_html=True)
    apply_date_range = st.sidebar.checkbox(
        "Enable date range",
        value=False,
        key="eo_apply_date_range",
    )

    start_date = None
    end_date = None
    if apply_date_range:
        start_date = st.sidebar.date_input(
            "Start Date",
            value=datetime.today().replace(day=1),
            key="eo_start_date",
        )
        end_date = st.sidebar.date_input(
            "End Date",
            value=datetime.today(),
            key="eo_end_date",
        )

        if start_date is not None and end_date is not None and end_date < start_date:
            st.sidebar.error("End Date cannot be earlier than Start Date")

    return {
        "drug_names": selected_drug_names,
        "therapeutic_categories": selected_therapeutic_categories,
        "customer_ids": selected_customer_ids,
        "year": int(selected_year) if selected_year not in ("Select Year", "All Years") else None,
        "month": month_options.index(selected_month) if selected_month not in ("Select Month", "All Months") else None,
        "start_date": start_date,
        "end_date": end_date,
    }

