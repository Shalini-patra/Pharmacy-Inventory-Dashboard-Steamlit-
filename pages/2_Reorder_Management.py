import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from lib.db import DatabaseManager
from lib.theme import ThemeManager
from lib.colors import ColorPalette
from lib.ui_overrides import green_banner, kpi_card
from lib.email_utils import EmailUtils
from lib.reorder_page_utils import get_reorder_filter_options, get_reorder_download_dataset

# Helper function for safe integer conversion
def safe_int(val, default=0):
    """Safely convert value to integer, handling NaN and other errors."""
    try:
        if pd.isna(val):
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

st.set_page_config(
    page_title="Reorder Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

ThemeManager.init_theme()
ThemeManager.apply_custom_css()

palette = ThemeManager.get_palette()
colors = ColorPalette.get_chart_colors()

# =========================
# Helpers (UI)
# =========================

BIN_GRADIENTS = {
    "Safe Stock": {
        "high": "#053B21",
        "low": "#458163"
    },

    "61-90 Days": {
        "high": "#E64C0F",
        "low": "#C57153"
    },

    "31-60 Days": {
        "high": "#F3AE0B",
        "low": "#DBB865"
    },

    "0-30 Days": {
        "high": "#DA120E",
        "low": "#CA8A82"
    }
}

# Lower-intensity value for matrix cells (used for styling)
SAFE_STOCK_LOW_INTENSITY = "#2E7D32"


ROW_COLORS = {
    "Immediate Reorder Needed": "#F00E0E",
    "Approaching Reorder": "#F5C61E",
    "Safe Stock": "#0E9144",
}

BIN_ORDER = ["0-30 Days", "31-60 Days", "61-90 Days", "Safe Stock"]


def interpolate_color(low_color, high_color, intensity):
    """
    intensity:
    0 = low color
    1 = high color
    """

    low_color = low_color.lstrip("#")
    high_color = high_color.lstrip("#")

    lr, lg, lb = (
        int(low_color[0:2], 16),
        int(low_color[2:4], 16),
        int(low_color[4:6], 16)
    )

    hr, hg, hb = (
        int(high_color[0:2], 16),
        int(high_color[2:4], 16),
        int(high_color[4:6], 16)
    )

    r = int(lr + (hr - lr) * intensity)
    g = int(lg + (hg - lg) * intensity)
    b = int(lb + (hb - lb) * intensity)

    return f"#{r:02X}{g:02X}{b:02X}"

def conditional_color_matrix(df_matrix: pd.DataFrame):

    """Apply Power BI-like conditional formatting by bin column.

    Expects df_matrix columns to be:
      therapeutic_category, 0-30 Days, 31-60 Days, 61-90 Days, Safe Stock
    """

    value_cols = [c for c in df_matrix.columns if c in BIN_ORDER]

    def style_cell(val, col):
        if pd.isna(val):
            return ""
        col_vals = df_matrix[col].dropna()
        if col_vals.empty:
            return ""
        vmin = float(col_vals.min())
        vmax = float(col_vals.max())
        if vmax <= vmin:
            intensity = 1.0
        else:
            intensity = np.sqrt((float(val) - vmin) / (vmax - vmin))
            intensity = max(0.0, min(1.0, intensity))

        # Keep low values visibly green (avoid almost-white).
        # Map intensity in [0,1] -> [0,1] then apply a floor.
        gradient = BIN_GRADIENTS[col]

        bg_color = interpolate_color(
            gradient["low"],
            gradient["high"],
            intensity
        )

        text_color = "#FFFFFF" if intensity > 0.45 else "#F5F5F5"

        return f"""
        background-color: {bg_color};
        color: {text_color};
        font-weight: 600;
        """
    styler = df_matrix.style

    for col in value_cols:
        styler = styler.map(
            lambda v, c=col: style_cell(v, c),
            subset=pd.IndexSlice[:, [col]]
        )

    # Header styling
    styler = styler.set_table_styles(
        [
            {"selector": "th", "props": [("color", palette['text_primary']), ("background-color", palette['surface'])]},
            {"selector": "td", "props": [("text-align", "right"), ("border", f"1px solid {palette['surface_light']}")]},
        ]
    )

    # Remove index label borders
    styler = styler.hide(axis="index")
    return styler


def copy_to_clipboard_js(text: str):

    """Inject a small snippet that copies `text` to the clipboard."""
    # Streamlit's components isn't imported in project; use unsafe HTML.
    st.markdown(
        f"""
        <script>
        async function bbCopy() {{
            try {{
                await navigator.clipboard.writeText({text!r});
                const ev = new Event('bbCopied');
                window.dispatchEvent(ev);
            }} catch (e) {{
                console.log(e);
                alert('Copy failed');
            }}
        }}
        bbCopy();
        </script>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Sidebar Filters (Power BI style)
# =========================

with st.sidebar:
    st.subheader("🔎 Filters")
    st.caption("Applies to Matrix and Action Table")

    filter_options = get_reorder_filter_options()
    all_categories = filter_options.get('therapeutic_categories', [])
    all_drug_ids = filter_options.get('drug_ids', [])
    all_drug_names = filter_options.get('drug_names', [])

    therapeutic_category = st.multiselect(
        "Therapeutic Category",
        options=all_categories,
        default=[],
        key="reorder_therapeutic_category",
        help="Select one or more categories to filter. Leave blank to include all categories.",
    )

    drug_id = st.multiselect(
        "Drug ID",
        options=all_drug_ids,
        default=[],
        key="reorder_drug_id",
        help="Select one or more drug IDs to filter. Leave blank to include all drugs.",
    )

    drug_name = st.multiselect(
        "Drug Name",
        options=all_drug_names,
        default=[],
        key="reorder_drug_name",
        help="Select one or more drug names to filter. Leave blank to include all drugs.",
    )

# Convert to None when all selected.
therapeutic_categories = therapeutic_category if therapeutic_category else None
filter_drug_ids = drug_id if drug_id else None
filter_drug_names = drug_name if drug_name else None

# =========================
# Page Header
# =========================

green_banner("📦 Reorder Management")
st.markdown("<div style='color:#D0D7DE; font-size:15px; margin-top:-10px; margin-bottom:18px;'>**Operational Inventory Management Center**</div>", unsafe_allow_html=True)

# ============== SECTION 1:  KPIs =============

try:
    action_rows_preview = DatabaseManager.get_reorder_action_rows(
        therapeutic_categories=therapeutic_categories,
        drug_ids=filter_drug_ids,
        drug_names=filter_drug_names,
    )

    # Ensure KPI counts are computed without emitting debug output.
    if action_rows_preview is not None and not action_rows_preview.empty:
        pass

    if not action_rows_preview.empty and 'stock_status' in action_rows_preview.columns:


        # KPI counts must be aligned with the same stock_status values used in get_reorder_action_rows().
        # IMPORTANT: The SQL in db.py maps to these exact labels.
        immediate_count = int((action_rows_preview['stock_status'] == 'Immediate Reorder Needed').sum())
        approaching_count = int((action_rows_preview['stock_status'] == 'Approaching Reorder').sum())
        safe_count = int((action_rows_preview['stock_status'] == 'Safe Stock').sum())

        col1, col2, col3 = st.columns(3, gap="small")
        with col1:
            kpi_card(
                label="Immediate Reorder",
                value=f"{immediate_count}",
                tooltip_pairs=[
                    ("What it measures", "Number of drugs requiring immediate reorder."),
                    ("Why it matters", "Shows urgent stock needs that must be replenished now."),
                ],
                icon="🔄",
                icon_color="danger",
                subtitle="Urgent replenishment",
            )
        with col2:
            kpi_card(
                label="Approaching Reorder",
                value=f"{approaching_count}",
                tooltip_pairs=[
                    ("What it measures", "Number of drugs nearing reorder threshold."),
                    ("Why it matters", "Highlights items that require close monitoring to avoid stockouts."),
                ],
                icon="⚠️",
                icon_color="warning",
                subtitle="Needs monitoring",
            )
        with col3:
            kpi_card(
                label="Safe Stock",
                value=f"{safe_count}",
                tooltip_pairs=[
                    ("What it measures", "Number of drugs currently above reorder levels."),
                    ("Why it matters", "Indicates healthy inventory coverage for stocked items."),
                ],
                icon="✅",
                icon_color="positive",
                subtitle="Healthy coverage",
            )

    else:

        immediate_count = 0
        approaching_count = 0
        safe_count = 0






except Exception as e:
    st.warning(f"⚠️ Could not compute KPI counts: {e}")

# ============== SECTION 2: Existing Reorder Alerts (keep) ==============
# Reuse the operational triage logic so KPIs + alerts + action table are consistent.

try:
    action_rows_for_alerts = DatabaseManager.get_reorder_action_rows(
        therapeutic_categories=therapeutic_categories,
        drug_ids=filter_drug_ids,
        drug_names=filter_drug_names,
    )

    if action_rows_for_alerts is None or action_rows_for_alerts.empty:
        st.success("✅ All drugs are in safe stock!")
    else:
        num_reorder = int((action_rows_for_alerts['stock_status'].isin([
            'Immediate Reorder Needed',
            'Approaching Reorder'
        ])).sum())

        if num_reorder > 0:
            st.error(f"🔴 **{num_reorder} DRUGS NEED REORDER TODAY**")
        else:
            st.success("✅ All drugs are in safe stock!")

except Exception as e:
    st.warning(f"⚠️ Could not compute reorder alerts: {e}")


# =========================
# SECTION 3: Inventory Shelf-Life Aging Matrix
# =========================

st.divider()
st.subheader("Inventory Shelf-Life Aging Matrix")

# Additional KPI Cards Above Matrix

try:
    # Use shelf-life bin aggregation to compute near-expiry units and value.
    # We'll reuse get_shelf_life_aging_matrix_by_therapeutic_category for units,
    # and compute value via a direct query using the existing expiry risk summary style.

    matrix_df = DatabaseManager.get_shelf_life_aging_matrix_by_therapeutic_category(
        therapeutic_categories=therapeutic_categories,
        drug_ids=filter_drug_ids,
        drug_names=filter_drug_names,
    )

    near_expiry_units = int(matrix_df[matrix_df['shelf_life_bin'] == '0-30 Days']['total_inventory_quantity'].sum()) if not matrix_df.empty else 0

    # Value KPI: compute from DB using expiry logic.
    # Use get_expiring_batches with 30 days and aggregate value from unit_cost_inr.
    expiring_30 = DatabaseManager.get_expiring_batches(days=30)
    if not expiring_30.empty:
        if therapeutic_categories is not None:
            expiring_30 = expiring_30[expiring_30['drug_id'].isin(filter_drug_ids)] if 'drug_id' in expiring_30.columns and filter_drug_ids is not None else expiring_30
        if filter_drug_ids is not None and 'drug_id' in expiring_30.columns:
            expiring_30 = expiring_30[expiring_30['drug_id'].isin(filter_drug_ids)]
        if filter_drug_names is not None and 'drug_name' in expiring_30.columns:
            expiring_30 = expiring_30[expiring_30['drug_name'].isin(filter_drug_names)]

    near_expiry_value = float(expiring_30['expiry_stock_value'].sum()) if not expiring_30.empty else 0.0

except Exception as e:
    matrix_df = pd.DataFrame()
    near_expiry_units = 0
    near_expiry_value = 0.0
    st.warning(f"⚠️ Shelf-life KPI computation warning: {e}")

k1, k2 = st.columns(2, gap="small")
with k1:
    kpi_card(
        label="Near Expiry Units (≤30 days)",
        value=f"{near_expiry_units}",
        tooltip_pairs=[
            ("What it measures", "Total units with 30 days or less remaining shelf life."),
            ("Why it matters", "Helps prioritize inventory that may expire soon."),
        ],
        icon="⏳",
        icon_color="warning",
        subtitle="Expiry risk units",
    )
with k2:
    kpi_card(
        label="Near Expiry Inventory Value (≤30 days)",
        value=f"₹{near_expiry_value:,.2f}",
        tooltip_pairs=[
            ("What it measures", "Monetary value of stock with 30 days or less remaining shelf life."),
            ("Why it matters", "Highlights potential expiry risk and reserve value."),
        ],
        icon="💸",
        icon_color="danger",
        subtitle="Expiry risk value",
    )

# Prepare matrix for display

if matrix_df.empty:
    st.info("No inventory data found for today with the selected filters.")
else:
    # Pivot to wide matrix
    wide = matrix_df.pivot_table(
        index='therapeutic_category',
        columns='shelf_life_bin',
        values='total_inventory_quantity',
        aggfunc='sum',
        fill_value=0,
    ).reset_index()

    # Ensure bin columns exist in correct order
    for b in BIN_ORDER:
        if b not in wide.columns:
            wide[b] = 0

    wide = wide[['therapeutic_category'] + BIN_ORDER]

    # Apply conditional formatting
    styler = conditional_color_matrix(wide)
    st.dataframe(styler, use_container_width=True, hide_index=True)

# =========================
# SECTION 4: Reorder Action Table
# =========================

st.divider()
st.subheader("Reorder Action Table")

try:
    action_rows = DatabaseManager.get_reorder_action_rows(
        therapeutic_categories=therapeutic_categories,
        drug_ids=filter_drug_ids,
        drug_names=filter_drug_names,
    )

    if action_rows.empty:
        st.info("No reorder action rows found for today with the selected filters.")
    else:
        # Required columns per spec
        table_df = action_rows.copy()
        table_df = table_df.rename(columns={
            'drug_id': 'Drug ID',
            'drug_name': 'Drug Name',
            'generic_name': 'Generic Name',
            'remaining_quantity': 'Remaining Quantity',
            'suggested_reorder_quantity': 'Suggested Reorder Quantity',
            'manufacturer_name': 'Manufacturer Name',
            'manufacturer_contact': 'Manufacturer Contact',
            'stock_status': 'Stock Status',
        })

        # Reorder columns exactly
        table_df = table_df[
            [
                'Stock Status',
                'Drug ID',
                'Drug Name',
                'Generic Name',
                'Remaining Quantity',
                'Suggested Reorder Quantity',
                'Manufacturer Name',
                'Manufacturer Contact',
            ]
        ]

        # Row coloring
        def row_bg(status):
            return ROW_COLORS.get(status, '')

        # Streamlit dataframe doesn't support per-row full background reliably via styling,
        # so use Styler.
        styler_rows = table_df.style
        for col in table_df.columns:
            # Apply formatting for value cells only; row background set via CSS.
            pass

        def apply_row_style(row):
            bg = row_bg(row['Stock Status'])
            return [f"background-color: {bg};" for _ in row]

        styler_rows = table_df.style.apply(apply_row_style, axis=1)

        st.dataframe(styler_rows, use_container_width=True, hide_index=True, height=420)

        # Copy functionality
        st.caption("Copy Selected Drug")
        selected_idx = st.selectbox(
            "Select a row (Drug Name + Drug ID)",
            options=(table_df['Drug Name'].astype(str) + " (" + table_df['Drug ID'].astype(str) + ")").tolist(),
            key='reorder_copy_select',
        )

        # Map selection back
        sel_row = table_df[table_df['Drug Name'].astype(str) + " (" + table_df['Drug ID'].astype(str) + ")" == selected_idx]
        if not sel_row.empty:
            sel_row = sel_row.iloc[0]

            copy_text = (
                f"Drug ID: {sel_row['Drug ID']}\n"
                f"Drug Name: {sel_row['Drug Name']}\n"
                f"Generic Name: {sel_row['Generic Name']}\n"
                f"Remaining Quantity: {safe_int(sel_row['Remaining Quantity'])}\n"
                f"Suggested Reorder Quantity: {safe_int(sel_row['Suggested Reorder Quantity'])}\n"
                f"Manufacturer Name: {sel_row['Manufacturer Name']}\n"
                f"Manufacturer Contact: {sel_row['Manufacturer Contact']}\n"
                f"Stock Status: {sel_row['Stock Status']}"
            )

            if st.button("📋 Copy Selected Drug", type='primary'):
                copy_to_clipboard_js(copy_text)
                st.success("Copied selected drug details to clipboard.")

except Exception as e:
    st.error(f"❌ Error loading reorder action table: {e}")

# =========================
# SECTION 5: Reorder Email & Automation Center
# =========================

st.divider()
st.subheader("Reorder Email & Automation Center")

imm_df = pd.DataFrame()
try:
    imm_df = get_reorder_download_dataset(
        therapeutic_categories=therapeutic_categories,
        drug_ids=filter_drug_ids,
        drug_names=filter_drug_names,
    )
except Exception as e:
    st.warning(f"⚠️ Could not load immediate reorder dataset: {e}")

csv_bytes = b""
if not imm_df.empty:
    csv_bytes = imm_df.to_csv(index=False).encode('utf-8')

manual_cols = st.columns(3)

# ACTION 1: Send Reorder Email
with manual_cols[0]:
    if st.button("📧 Send Reorder Email"):
        if imm_df.empty:
            st.info("No immediate reorder rows are available for the current filters yet.")
        else:
            try:
                EmailUtils.send_reorder_email_with_csv(
                    csv_bytes=csv_bytes,
                    filename=f"reorder_list_immediate_{datetime.now().strftime('%Y%m%d')}.csv",
                    subject="Pharmacy Reorder Alert",
                    body_text=(
                        "These drugs need to be reordered.\n\n"
                        "Please find the attached CSV file containing reorder details.\n\n"
                        "Generated automatically by the Pharmacy Smart Inventory System."
                    ),
                )
                st.success("✅ Reorder email sent successfully.")
            except Exception as e:
                st.error(f"❌ Failed to send reorder email: {e}")


# ACTION 2: Download Reorder List
with manual_cols[1]:
    st.download_button(
        label="⬇ Download Reorder List",
        data=csv_bytes,
        file_name=f"reorder_list_immediate_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

# ACTION 3: Automated Daily Reorder Email (separate automation script)
with manual_cols[2]:
    st.info(
        "Automated daily reorder email is configured via: automation/daily_reorder_email.py\n"
        "Schedule recommendation: daily at 9:00 AM"
    )


st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data from NeonDB")

