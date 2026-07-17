from __future__ import annotations

import pandas as pd
from typing import Optional

from lib.db import DatabaseManager


def _coerce_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def apply_executive_overview_filters(df: pd.DataFrame, filters: Optional[dict] = None) -> pd.DataFrame:
    """Apply sidebar filters to a transaction-level DataFrame once and reuse it everywhere."""
    filters = filters or {}
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    filtered_df = df.copy()
    if filtered_df.empty:
        return filtered_df

    if "transaction_date" in filtered_df.columns:
        filtered_df["transaction_date"] = _coerce_datetime(filtered_df["transaction_date"])
        filtered_df = filtered_df.dropna(subset=["transaction_date"]).copy()

    customer_ids = filters.get("customer_ids") or []
    drug_names = filters.get("drug_names") or []
    therapeutic_categories = filters.get("therapeutic_categories") or []
    year = filters.get("year")
    month = filters.get("month")
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")

    if customer_ids and "customer_id" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["customer_id"].isin(customer_ids)]

    if drug_names and "drug_name" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["drug_name"].isin(drug_names)]

    if therapeutic_categories and "therapeutic_category" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["therapeutic_category"].isin(therapeutic_categories)]

    if year is not None:
        filtered_df = filtered_df[filtered_df["transaction_date"].dt.year == int(year)]

    if month is not None:
        filtered_df = filtered_df[filtered_df["transaction_date"].dt.month == int(month)]

    if start_date is not None:
        filtered_df = filtered_df[filtered_df["transaction_date"] >= pd.Timestamp(start_date)]

    if end_date is not None:
        filtered_df = filtered_df[filtered_df["transaction_date"] <= pd.Timestamp(end_date)]

    return filtered_df


def get_executive_overview_master_dataframe(filters: Optional[dict] = None, months: int = 12) -> pd.DataFrame:
    """Load one shared filtered dataset for the full Executive Overview page."""
    filters = filters or {}
    df = DatabaseManager.get_executive_overview_master_data(months=months)
    return apply_executive_overview_filters(df, filters)


def get_filtered_top_moving_drugs(filters: Optional[dict] = None, days: int = 30, limit: int = 5) -> pd.DataFrame:
    filters = filters or {}
    return DatabaseManager.get_top_moving_drugs_filtered(
        days=days,
        limit=limit,
        drug_names=filters.get("drug_names"),
        therapeutic_categories=filters.get("therapeutic_categories"),
        customer_names=filters.get("customer_names"),
        year=filters.get("year"),
        month=filters.get("month"),
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
    )


def get_filtered_bottom_moving_drugs(filters: Optional[dict] = None, days: int = 30, limit: int = 5) -> pd.DataFrame:
    filters = filters or {}
    return DatabaseManager.get_bottom_moving_drugs_filtered(
        days=days,
        limit=limit,
        drug_names=filters.get("drug_names"),
        therapeutic_categories=filters.get("therapeutic_categories"),
        customer_names=filters.get("customer_names"),
        year=filters.get("year"),
        month=filters.get("month"),
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
    )


def get_filtered_monthly_revenue_profit_trend(filters: Optional[dict] = None, months: int = 12):
    filters = filters or {}
    return DatabaseManager.get_monthly_revenue_profit_trend_filtered(
        months=months,
        drug_names=filters.get("drug_names"),
        therapeutic_categories=filters.get("therapeutic_categories"),
        customer_names=filters.get("customer_names"),
        year=filters.get("year"),
        month=filters.get("month"),
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
    )


def get_filtered_monthly_customer_metrics(filters: Optional[dict] = None, months: int = 12):
    filters = filters or {}
    return DatabaseManager.get_monthly_customer_metrics_filtered(
        months=months,
        drug_names=filters.get("drug_names"),
        therapeutic_categories=filters.get("therapeutic_categories"),
        customer_names=filters.get("customer_names"),
        year=filters.get("year"),
        month=filters.get("month"),
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
    )


def get_filtered_weekday_hour_heatmap(filters: Optional[dict] = None, months: int = 12):
    filters = filters or {}
    return DatabaseManager.get_weekday_hour_heatmap_filtered(
        months=months,
        drug_names=filters.get("drug_names"),
        therapeutic_categories=filters.get("therapeutic_categories"),
        customer_names=filters.get("customer_names"),
        year=filters.get("year"),
        month=filters.get("month"),
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
    )

