from __future__ import annotations

import pandas as pd
from typing import Optional
from lib.db import DatabaseManager


def get_filtered_top_moving_drugs(filters: Optional[dict] = None, days: int = 30, limit: int = 5) -> pd.DataFrame:
    """Filter-aware top moving drugs.

    Preserves existing DB connectivity + caching by delegating to DatabaseManager
    helpers when available.
    """
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

