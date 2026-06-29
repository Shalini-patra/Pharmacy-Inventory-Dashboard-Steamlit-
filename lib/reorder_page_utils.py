from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from lib.db import DatabaseManager


def normalize_filter_options(values: Any) -> List[Any]:
    """Return a sorted, de-duplicated list of filter values for Streamlit widgets."""
    if values is None:
        return []
    if isinstance(values, pd.Series):
        values = values.tolist()
    if not isinstance(values, list):
        values = [values]

    cleaned: List[Any] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        if isinstance(value, str) and not value.strip():
            continue
        cleaned.append(value)

    if not cleaned:
        return []

    return sorted(set(cleaned), key=lambda item: str(item))


def get_reorder_filter_options() -> Dict[str, List[Any]]:
    """Build consistent filter option lists for the reorder management page."""
    try:
        drug_names = DatabaseManager.get_distinct_drug_names()
    except Exception:
        drug_names = []

    try:
        therapeutic_categories = DatabaseManager.get_distinct_therapeutic_categories()
    except Exception:
        therapeutic_categories = []

    try:
        heatmap_df = DatabaseManager.get_inventory_heatmap_data()
    except Exception:
        heatmap_df = pd.DataFrame()

    drug_ids = []
    if not heatmap_df.empty and 'drug_id' in heatmap_df.columns:
        drug_ids = normalize_filter_options(heatmap_df['drug_id'].dropna())

    if not drug_names:
        if not heatmap_df.empty and 'drug_name' in heatmap_df.columns:
            drug_names = normalize_filter_options(heatmap_df['drug_name'].dropna())

    if not therapeutic_categories:
        if not heatmap_df.empty and 'therapeutic_category' in heatmap_df.columns:
            therapeutic_categories = normalize_filter_options(heatmap_df['therapeutic_category'].dropna())

    return {
        'drug_ids': drug_ids,
        'drug_names': normalize_filter_options(drug_names),
        'therapeutic_categories': normalize_filter_options(therapeutic_categories),
    }


def get_reorder_download_dataset(
    therapeutic_categories: Optional[List[str]] = None,
    drug_ids: Optional[List[str]] = None,
    drug_names: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Return a CSV-ready immediate reorder dataset, with a graceful fallback."""
    try:
        immediate_df = DatabaseManager.get_immediate_reorder_csv_dataset(
            therapeutic_categories=therapeutic_categories,
            drug_ids=drug_ids,
            drug_names=drug_names,
        )
    except Exception:
        immediate_df = pd.DataFrame()

    if immediate_df is not None and not immediate_df.empty:
        return immediate_df

    try:
        action_rows = DatabaseManager.get_reorder_action_rows(
            therapeutic_categories=therapeutic_categories,
            drug_ids=drug_ids,
            drug_names=drug_names,
        )
    except Exception:
        action_rows = pd.DataFrame()

    if action_rows is None or action_rows.empty:
        return pd.DataFrame(columns=[
            'drug_id',
            'drug_name',
            'suggested_reorder_quantity',
            'manufacturer_name',
            'manufacturer_contact',
        ])

    immediate_rows = action_rows[action_rows['stock_status'].isin(['Immediate Reorder Needed'])].copy()
    if immediate_rows.empty:
        return pd.DataFrame(columns=[
            'drug_id',
            'drug_name',
            'suggested_reorder_quantity',
            'manufacturer_name',
            'manufacturer_contact',
        ])

    immediate_rows = immediate_rows.rename(columns={
        'drug_id': 'drug_id',
        'drug_name': 'drug_name',
        'suggested_reorder_quantity': 'suggested_reorder_quantity',
        'manufacturer_name': 'manufacturer_name',
        'manufacturer_contact': 'manufacturer_contact',
    })

    return immediate_rows[['drug_id', 'drug_name', 'suggested_reorder_quantity', 'manufacturer_name', 'manufacturer_contact']].copy()
