# lib/db.py
import streamlit as st
import psycopg2
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """Manages all database connections and queries."""

    # ===================== Executive Overview: Filter Helpers =====================

    @staticmethod
    def _eo_norm_optional_list(values: Optional[List[str]]):
        """Normalize empty lists from UI into None so SQL optional filters behave."""
        if values is None:
            return None
        if isinstance(values, list) and len(values) == 0:
            return None
        return values

    @staticmethod
    def _eo_apply_filters(
        base_where: str,
        params: list,
        *,
        drug_names: Optional[List[str]] = None,
        therapeutic_categories: Optional[List[str]] = None,
        customer_names: Optional[List[str]] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """Build optional filters for Executive Overview.

        Returns: (where_sql, params)

        Notes:
        - All optional list filters use Postgres ANY(%s).
        - Date filters use transaction_date.
        """
        where_sql = base_where

        if therapeutic_categories:
            where_sql += " AND d.therapeutic_category = ANY(%s)"
            params.append(therapeutic_categories)

        if drug_names:
            where_sql += " AND d.drug_name = ANY(%s)"
            params.append(drug_names)

        if customer_names:
            where_sql += " AND c.customer_name = ANY(%s)"
            params.append(customer_names)

        if year is not None:
            where_sql += " AND EXTRACT(YEAR FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(year))

        if month is not None:
            where_sql += " AND EXTRACT(MONTH FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(month))

        if start_date is not None:
            where_sql += " AND CAST(dt.transaction_date AS DATE) >= %s"
            params.append(start_date)

        if end_date is not None:
            where_sql += " AND CAST(dt.transaction_date AS DATE) <= %s"
            params.append(end_date)

        return where_sql, params


    # ===================== Executive Overview: Filter Helpers =====================

    @staticmethod
    def _eo_norm_optional_list(values: Optional[List[str]]):
        if values is None:
            return None
        if isinstance(values, list) and len(values) == 0:
            return None
        return values


    @staticmethod
    def _none_if_empty(values: Optional[List[str]]):
        """Normalize empty lists from UI into None so SQL optional filters behave."""
        if not values:
            return None
        return values

    @staticmethod
    def _get_db_config() -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Resolve DB credentials from Streamlit secrets or environment variables."""
        secret_values = {}

        secrets_obj = getattr(st, 'secrets', None)
        if secrets_obj is not None:
            try:
                if hasattr(secrets_obj, 'to_dict'):
                    secret_values = secrets_obj.to_dict()
                elif isinstance(secrets_obj, dict):
                    secret_values = dict(secrets_obj)
                elif hasattr(secrets_obj, 'get'):
                    secret_values = dict(secrets_obj)
            except Exception:
                secret_values = {}

        def _get_value(*keys: str):
            for key in keys:
                if not key:
                    continue
                if isinstance(secret_values, dict):
                    if key in secret_values and secret_values[key] not in (None, ''):
                        return secret_values[key]
                    if key.lower() in secret_values and secret_values[key.lower()] not in (None, ''):
                        return secret_values[key.lower()]
                    nested = secret_values.get('neondb')
                    if isinstance(nested, dict):
                        if key in nested and nested[key] not in (None, ''):
                            return nested[key]
                        if key.lower() in nested and nested[key.lower()] not in (None, ''):
                            return nested[key.lower()]

            env_key = None
            for key in keys:
                if not key:
                    continue
                env_key = os.getenv(key)
                if env_key:
                    return env_key
            return None

        host = _get_value('NEON_HOST', 'HOST', 'host')
        database = _get_value('NEON_DATABASE', 'DATABASE', 'database')
        user = _get_value('NEON_USER', 'USER', 'user')
        password = _get_value('NEON_PASSWORD', 'PASSWORD', 'password')

        return host, database, user, password

    @staticmethod
    def get_connection():
        """
        Create a fresh database connection every time.
        """
        try:
            host, database, user, password = DatabaseManager._get_db_config()

            if not all([host, database, user, password]):
                raise RuntimeError(
                    'Database credentials not found. Set NEON_HOST, NEON_DATABASE, NEON_USER, NEON_PASSWORD '
                    'as environment variables or add them to Streamlit secrets.'
                )

            conn = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                sslmode='require',
                connect_timeout=5,
            )
            return conn

        except Exception as e:
            # Raise a runtime error so calling pages can catch and show a consistent message.
            raise RuntimeError(f'Database connection failed: {str(e)}') from e

    @staticmethod
    def _read_sql_safe(query: str, params: list | None = None):
        """Run a read query safely and return a DataFrame or empty DataFrame on error.

        This centralizes connection handling so pages don't get NoneType cursor errors
        when the database is unreachable (for example in deployments without secrets).
        """
        try:
            conn = DatabaseManager.get_connection()
        except Exception as e:
            # Show a friendly message to the user and return an empty DataFrame
            try:
                st.error(f"❌ Database connection failed: {str(e)}")
            except Exception:
                pass
            return pd.DataFrame()

        if conn is None:
            try:
                st.error("❌ Database connection unavailable. Check configuration.")
            except Exception:
                pass
            return pd.DataFrame()

        try:
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception:
            try:
                st.error("❌ Query failed. Please try again later.")
            except Exception:
                pass
            return pd.DataFrame()
        finally:
            try:
                conn.close()
            except Exception:
                pass

    
    @staticmethod
    def test_connection() -> bool:
        try:
            conn = DatabaseManager.get_connection()

            if conn is not None:
                conn.close()
                return True

            return False

        except Exception:
            return False
    
    # ============== EXECUTIVE OVERVIEW QUERIES ==============

    @staticmethod
    def _apply_optional_array_filters(sql_where: str, params: list, field: str, values: Optional[List[str]]):
        """Helper to append optional ANY(...) filters using parameter binding."""
        if values:
            sql_where += f" AND {field} = ANY(%s)"
            params.append(values)
        return sql_where, params

    @staticmethod
    def _normalize_filter_list(values: Optional[list]):
        if values is None:
            return None
        if isinstance(values, list) and len(values) == 0:
            return None
        return values

    @staticmethod
    @st.cache_data(ttl=600)
    def get_distinct_drug_names():
        query = "SELECT DISTINCT drug_name FROM drugs ORDER BY drug_name;"
        df = DatabaseManager._read_sql_safe(query)
        return df["drug_name"].tolist() if not df.empty else []

    @staticmethod
    @st.cache_data(ttl=600)
    def get_distinct_therapeutic_categories():
        query = "SELECT DISTINCT therapeutic_category FROM drugs ORDER BY therapeutic_category;"
        df = DatabaseManager._read_sql_safe(query)
        return df["therapeutic_category"].tolist() if not df.empty else []

    @staticmethod
    @st.cache_data(ttl=600)
    def get_distinct_customer_names():
        query = "SELECT DISTINCT customer_name FROM customers ORDER BY customer_name;"
        df = DatabaseManager._read_sql_safe(query)
        return df["customer_name"].tolist() if not df.empty else []

    @staticmethod
    @st.cache_data(ttl=600)
    def get_distinct_years():
        query = "SELECT DISTINCT EXTRACT(YEAR FROM CAST(transaction_date AS DATE))::INT AS year FROM transactions WHERE transaction_type = 'Sale' ORDER BY year DESC;"
        df = DatabaseManager._read_sql_safe(query)
        return df["year"].tolist() if not df.empty else []

    @staticmethod
    @st.cache_data(ttl=300)
    def get_top_moving_drugs_filtered(
        days: int = 30,
        limit: int = 5,
        drug_names: Optional[list] = None,
        therapeutic_categories: Optional[list] = None,
        customer_names: Optional[list] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        conn = DatabaseManager.get_connection()
        params: list = []
        query = f"""
        SELECT
            d.drug_id,
            d.drug_name,
            d.therapeutic_category,
            SUM(dt.quantity) AS total_units,
            SUM(dt.total_value_inr) AS total_revenue,
            ROUND((SUM(dt.total_value_inr) / NULLIF({days}, 0))::numeric, 2) AS avg_daily_revenue,
            a.abc_class
        FROM transactions dt
        JOIN drugs d ON dt.drug_id = d.drug_id
        LEFT JOIN abc_analysis a ON d.drug_id = a.drug_id
        LEFT JOIN customers c ON dt.customer_id = c.customer_id
        WHERE dt.transaction_type = 'Sale'
          AND CAST(dt.transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '{days} days'
        """
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.drug_name', DatabaseManager._normalize_filter_list(drug_names))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.therapeutic_category', DatabaseManager._normalize_filter_list(therapeutic_categories))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'c.customer_name', DatabaseManager._normalize_filter_list(customer_names))
        if year is not None:
            query += " AND EXTRACT(YEAR FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(year))
        if month is not None:
            query += " AND EXTRACT(MONTH FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(month))
        if start_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) >= %s"
            params.append(start_date)
        if end_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) <= %s"
            params.append(end_date)
        query += " GROUP BY d.drug_id, d.drug_name, d.therapeutic_category, a.abc_class"
        query += " ORDER BY total_units DESC, total_revenue DESC LIMIT %s;"
        params.append(limit)
        df = DatabaseManager._read_sql_safe(query, params=params)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_bottom_moving_drugs_filtered(
        days: int = 30,
        limit: int = 5,
        drug_names: Optional[list] = None,
        therapeutic_categories: Optional[list] = None,
        customer_names: Optional[list] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        conn = DatabaseManager.get_connection()
        params: list = []
        query = f"""
        SELECT
            d.drug_id,
            d.drug_name,
            d.therapeutic_category,
            SUM(dt.quantity) AS total_units,
            SUM(dt.total_value_inr) AS total_revenue,
            ROUND((SUM(dt.total_value_inr) / NULLIF({days}, 0))::numeric, 2) AS avg_daily_revenue,
            a.abc_class
        FROM transactions dt
        JOIN drugs d ON dt.drug_id = d.drug_id
        LEFT JOIN abc_analysis a ON d.drug_id = a.drug_id
        LEFT JOIN customers c ON dt.customer_id = c.customer_id
        WHERE dt.transaction_type = 'Sale'
        """
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.drug_name', DatabaseManager._normalize_filter_list(drug_names))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.therapeutic_category', DatabaseManager._normalize_filter_list(therapeutic_categories))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'c.customer_name', DatabaseManager._normalize_filter_list(customer_names))
        if year is not None:
            query += " AND EXTRACT(YEAR FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(year))
        if month is not None:
            query += " AND EXTRACT(MONTH FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(month))
        if start_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) >= %s"
            params.append(start_date)
        if end_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) <= %s"
            params.append(end_date)
        query += " GROUP BY d.drug_id, d.drug_name, d.therapeutic_category, a.abc_class"
        query += " HAVING SUM(dt.total_value_inr) > 0"
        query += " ORDER BY total_units ASC, total_revenue ASC LIMIT %s;"
        params.append(limit)
        df = DatabaseManager._read_sql_safe(query, params=params)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_monthly_revenue_profit_trend_filtered(
        months: int = 12,
        drug_names: Optional[list] = None,
        therapeutic_categories: Optional[list] = None,
        customer_names: Optional[list] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        conn = DatabaseManager.get_connection()
        params: list = []
        query = f"""
        SELECT
            DATE_TRUNC('month', CAST(dt.transaction_date AS DATE))::DATE AS month,
            SUM(dt.total_value_inr) AS total_revenue,
            SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) AS total_profit
        FROM transactions dt
        JOIN drugs d ON dt.drug_id = d.drug_id
        LEFT JOIN customers c ON dt.customer_id = c.customer_id
        WHERE dt.transaction_type = 'Sale'
          AND CAST(dt.transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '{months} months'
        """
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.drug_name', DatabaseManager._normalize_filter_list(drug_names))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.therapeutic_category', DatabaseManager._normalize_filter_list(therapeutic_categories))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'c.customer_name', DatabaseManager._normalize_filter_list(customer_names))
        if year is not None:
            query += " AND EXTRACT(YEAR FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(year))
        if month is not None:
            query += " AND EXTRACT(MONTH FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(month))
        if start_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) >= %s"
            params.append(start_date)
        if end_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) <= %s"
            params.append(end_date)
        query += " GROUP BY month ORDER BY month ASC;"
        df = DatabaseManager._read_sql_safe(query, params=params)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_monthly_customer_metrics_filtered(
        months: int = 12,
        drug_names: Optional[list] = None,
        therapeutic_categories: Optional[list] = None,
        customer_names: Optional[list] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        conn = DatabaseManager.get_connection()
        params: list = []
        query = f"""
        SELECT
            DATE_TRUNC('month', CAST(dt.transaction_date AS DATE))::DATE AS month,
            COUNT(DISTINCT dt.customer_id) AS unique_customers,
            COUNT(DISTINCT dt.transaction_id) AS total_transactions
        FROM transactions dt
        LEFT JOIN customers c ON dt.customer_id = c.customer_id
        LEFT JOIN drugs d ON dt.drug_id = d.drug_id
        WHERE dt.transaction_type = 'Sale'
          AND CAST(dt.transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '{months} months'
        """
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.drug_name', DatabaseManager._normalize_filter_list(drug_names))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'd.therapeutic_category', DatabaseManager._normalize_filter_list(therapeutic_categories))
        query, params = DatabaseManager._apply_optional_array_filters(query, params, 'c.customer_name', DatabaseManager._normalize_filter_list(customer_names))
        if year is not None:
            query += " AND EXTRACT(YEAR FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(year))
        if month is not None:
            query += " AND EXTRACT(MONTH FROM CAST(dt.transaction_date AS DATE)) = %s"
            params.append(int(month))
        if start_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) >= %s"
            params.append(start_date)
        if end_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) <= %s"
            params.append(end_date)
        query += " GROUP BY month ORDER BY month ASC;"
        df = DatabaseManager._read_sql_safe(query, params=params)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_weekday_hour_heatmap_filtered(
        months: int = 12,
        drug_names: Optional[list] = None,
        therapeutic_categories: Optional[list] = None,
        customer_names: Optional[list] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        conn = DatabaseManager.get_connection()
        params: list = []
        query = f"""
        SELECT
            weekday,
            hour_bin,
            COUNT(DISTINCT transaction_id) AS transaction_count,
            MIN(ordering) AS ordering
        FROM (
            SELECT
                dt.transaction_id,
                dt.transaction_date,
                d.drug_name,
                d.therapeutic_category,
                c.customer_name,
                CASE
                    WHEN EXTRACT(DOW FROM CAST(dt.transaction_date AS TIMESTAMP))::INT = 1 THEN 'Monday'
                    WHEN EXTRACT(DOW FROM CAST(dt.transaction_date AS TIMESTAMP))::INT = 2 THEN 'Tuesday'
                    WHEN EXTRACT(DOW FROM CAST(dt.transaction_date AS TIMESTAMP))::INT = 3 THEN 'Wednesday'
                    WHEN EXTRACT(DOW FROM CAST(dt.transaction_date AS TIMESTAMP))::INT = 4 THEN 'Thursday'
                    WHEN EXTRACT(DOW FROM CAST(dt.transaction_date AS TIMESTAMP))::INT = 5 THEN 'Friday'
                    WHEN EXTRACT(DOW FROM CAST(dt.transaction_date AS TIMESTAMP))::INT = 6 THEN 'Saturday'
                    ELSE 'Sunday'
                END AS weekday,
                CASE
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 0 THEN '0-2'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 1 THEN '2-4'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 2 THEN '4-6'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 3 THEN '6-8'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 4 THEN '8-10'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 5 THEN '10-12'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 6 THEN '12-14'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 7 THEN '14-16'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 8 THEN '16-18'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 9 THEN '18-20'
                    WHEN FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT = 10 THEN '20-22'
                    ELSE '22-24'
                END AS hour_bin,
                FLOOR(EXTRACT(HOUR FROM CAST(dt.transaction_date AS TIMESTAMP)) / 2)::INT AS ordering
            FROM transactions dt
            JOIN drugs d ON dt.drug_id = d.drug_id
            LEFT JOIN customers c ON dt.customer_id = c.customer_id
            WHERE dt.transaction_type = 'Sale'
              AND CAST(dt.transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '{months} months'
        ) AS sub
        WHERE 1=1
        """
        if drug_names:
            query += " AND drug_name = ANY(%s)"
            params.append(DatabaseManager._normalize_filter_list(drug_names))
        if therapeutic_categories:
            query += " AND therapeutic_category = ANY(%s)"
            params.append(DatabaseManager._normalize_filter_list(therapeutic_categories))
        if customer_names:
            query += " AND customer_name = ANY(%s)"
            params.append(DatabaseManager._normalize_filter_list(customer_names))
        if year is not None:
            query += " AND EXTRACT(YEAR FROM CAST(transaction_date AS DATE)) = %s"
            params.append(int(year))
        if month is not None:
            query += " AND EXTRACT(MONTH FROM CAST(transaction_date AS DATE)) = %s"
            params.append(int(month))
        if start_date is not None:
            query += " AND CAST(transaction_date AS DATE) >= %s"
            params.append(start_date)
        if end_date is not None:
            query += " AND CAST(transaction_date AS DATE) <= %s"
            params.append(end_date)
        query += " GROUP BY weekday, hour_bin, ordering ORDER BY ordering, hour_bin;"
        df = DatabaseManager._read_sql_safe(query, params=params)
        return df

    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_top_moving_drugs(days: int = 30, limit: int = 5):

        """Get top 5 moving drugs by revenue in last N days."""
        conn = DatabaseManager.get_connection()
        query = f"""
        SELECT 
            d.drug_id,
            d.drug_name,
            d.therapeutic_category,
            SUM(dt.quantity) as total_units,
            SUM(dt.total_value_inr) as total_revenue,
            ROUND(
                 (SUM(dt.total_value_inr) / {days})::numeric,
                  2
             ) as avg_daily_revenue,
            a.abc_class
        FROM transactions dt
        JOIN drugs d ON dt.drug_id = d.drug_id
        LEFT JOIN abc_analysis a ON d.drug_id = a.drug_id
        WHERE CAST(dt.transaction_date AS DATE)>= CURRENT_DATE - INTERVAL '{days} days'
          AND dt.transaction_type = 'Sale'
        GROUP BY d.drug_id, d.drug_name, d.therapeutic_category, a.abc_class
        ORDER BY total_revenue DESC
        LIMIT {limit};
        """
        df = DatabaseManager._read_sql_safe(query)
        return df

    # ============== REORDER MANAGEMENT (FILTERED + OPERATIONAL CENTER) ==============

    @staticmethod
    @st.cache_data(ttl=300)
    def get_shelf_life_aging_matrix_by_therapeutic_category(
        therapeutic_categories: Optional[List[str]] = None,
        drug_ids: Optional[List[str]] = None,
        drug_names: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Return shelf-life aging matrix aggregation:
        therapeutic_category x shelf_life_bin with values = SUM(remaining_stock).

        Shelf life bin is computed from remaining_shelf_life_days = expiry_date - CURRENT_DATE.

        Bins:
          - 0-30 Days
          - 31-60 Days
          - 61-90 Days
          - Safe Stock (>90 Days)
        """

        conn = DatabaseManager.get_connection()

        # Build optional filters safely for lists.
        # Note: drug_names are treated as exact matches for selected options.
        categories_filter = ""
        if therapeutic_categories:
            categories_filter = " AND d.therapeutic_category = ANY(%s) "

        drug_ids_filter = ""
        if drug_ids:
            drug_ids_filter = " AND d.drug_id = ANY(%s) "

        drug_names_filter = ""
        if drug_names:
            # ILIKE matching is handled in Streamlit by passing selected names.
            drug_names_filter = " AND d.drug_name = ANY(%s) "

        query = f"""
        WITH base AS (
            SELECT
                d.therapeutic_category,
                d.drug_id,
                d.drug_name,
                i.remaining_stock,
                CASE
                    WHEN i.expiry_date IS NULL THEN 999999
                    ELSE GREATEST((i.expiry_date::date - CURRENT_DATE), 0)::INT

                END AS remaining_shelf_life_days
            FROM inventory_snapshots i
            JOIN drugs d ON i.drug_id = d.drug_id
            WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
        )
        SELECT
            b.therapeutic_category,
            CASE
                WHEN b.remaining_shelf_life_days <= 30 THEN '0-30 Days'
                WHEN b.remaining_shelf_life_days <= 60 THEN '31-60 Days'
                WHEN b.remaining_shelf_life_days <= 90 THEN '61-90 Days'
                ELSE 'Safe Stock'
            END AS shelf_life_bin,
            SUM(b.remaining_stock)::INT AS total_inventory_quantity
        FROM base b
        JOIN drugs d ON d.drug_id = b.drug_id
        WHERE 1=1
            {('' if not therapeutic_categories else 'AND d.therapeutic_category = ANY(%s)')}
            {('' if not drug_ids else 'AND d.drug_id = ANY(%s)')}
            {('' if not drug_names else 'AND d.drug_name = ANY(%s)')}
        GROUP BY b.therapeutic_category, shelf_life_bin
        ORDER BY b.therapeutic_category, shelf_life_bin;
        """

        params = []
        if therapeutic_categories:
            params.append(therapeutic_categories)
        if drug_ids:
            params.append(drug_ids)
        if drug_names:
            params.append(drug_names)

        # Use safe read helper with params.
        df = DatabaseManager._read_sql_safe(query, params=params if params else None)

        # Ensure consistent bins order.
        bin_order = ['0-30 Days', '31-60 Days', '61-90 Days', 'Safe Stock']
        if not df.empty:
            df['shelf_life_bin'] = pd.Categorical(df['shelf_life_bin'], categories=bin_order, ordered=True)
            df = df.sort_values(['therapeutic_category', 'shelf_life_bin'])

        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_reorder_action_rows(
        therapeutic_categories: Optional[List[str]] = None,
        drug_ids: Optional[List[str]] = None,
        drug_names: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Return operational reorder rows with triage and required sorting.

        Stock Status logic (based on remaining_stock vs reorder_point):
          - Immediate Reorder Needed: remaining_stock <= reorder_point
          - Approaching Reorder: remaining_stock <= reorder_point*1.25 AND remaining_stock > reorder_point
          - Safe Stock: remaining_stock > reorder_point*1.25
        """

        conn = DatabaseManager.get_connection()

        query = """
        WITH base AS (
            SELECT
                d.drug_id,
                d.drug_name,
                d.generic_name,
                d.manufacturer_name,
                d.manufacturer_phone AS manufacturer_contact,
                d.therapeutic_category,
                COALESCE(r.reorder_point, 0)::INT AS reorder_point,
                COALESCE(r.suggested_reorder_qty, 0)::INT AS suggested_reorder_quantity,
                s.lead_time_days,
                COALESCE(SUM(i.remaining_stock), 0)::INT AS remaining_quantity
            FROM inventory_snapshots i
            JOIN drugs d ON i.drug_id = d.drug_id
            JOIN reorder_points r ON i.drug_id = r.drug_id
            LEFT JOIN lead_times s ON i.drug_id = s.drug_id
            WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
            GROUP BY
                d.drug_id,
                d.drug_name,
                d.generic_name,
                d.manufacturer_name,
                d.manufacturer_phone,
                d.therapeutic_category,
                r.reorder_point,
                r.suggested_reorder_qty,
                s.lead_time_days
        )
        SELECT
            CASE
                WHEN b.reorder_point <= 0 THEN 'Safe'
                WHEN b.remaining_quantity <= b.reorder_point THEN 'Immediate'
                WHEN b.remaining_quantity <= (b.reorder_point * 1.25) AND b.remaining_quantity > b.reorder_point THEN 'Approaching'
                ELSE 'Safe'
            END AS stock_status_group,

            b.drug_id,
            b.drug_name,
            b.generic_name,
            b.remaining_quantity,
            b.suggested_reorder_quantity,
            b.manufacturer_name,
            b.manufacturer_contact,
            b.therapeutic_category,
            b.reorder_point,
            CURRENT_DATE AS snapshot_date,
            b.lead_time_days
        FROM base b
        WHERE 1=1
        """

        params = []

        if therapeutic_categories:
            query += " AND b.therapeutic_category = ANY(%s)"
            params.append(therapeutic_categories)

        if drug_ids:
            query += " AND b.drug_id = ANY(%s)"
            params.append(drug_ids)

        if drug_names:
            query += " AND b.drug_name = ANY(%s)"
            params.append(drug_names)

        # NOTE: Do not ORDER BY the alias `stock_status_group` because some Postgres builds/scopes
        # fail to resolve it reliably. Repeat the CASE expression instead.
        query += """
        ORDER BY
CASE
                WHEN b.remaining_quantity <= b.reorder_point THEN 1
                WHEN b.remaining_quantity <= (b.reorder_point * 1.25)
                     AND b.remaining_quantity > b.reorder_point THEN 2
                ELSE 3
            END,
            remaining_quantity ASC;
        """


        df = DatabaseManager._read_sql_safe(query, params=params if params else None)

        if df.empty:
            return df

        # Map group to UI labels.
        df['stock_status'] = df['stock_status_group'].map({
            'Immediate': 'Immediate Reorder Needed',
            'Approaching': 'Approaching Reorder',
            'Safe': 'Safe Stock'
        })

        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_immediate_reorder_csv_dataset(
        therapeutic_categories: Optional[List[str]] = None,
        drug_ids: Optional[List[str]] = None,
        drug_names: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Dataset for CSV/email: only drugs that require immediate reorder.

        Returns one row per drug_id (deduped) suitable for email/download CSV.
        """

        conn = DatabaseManager.get_connection()

        query = """
        WITH base AS (
            SELECT
                d.drug_id,
                d.drug_name,
                d.therapeutic_category,
                COALESCE(r.suggested_reorder_qty, 0)::INT AS suggested_reorder_quantity,
                d.manufacturer_name,
                d.manufacturer_phone AS manufacturer_contact
            FROM inventory_snapshots i
            JOIN drugs d ON i.drug_id = d.drug_id
            JOIN reorder_points r ON i.drug_id = r.drug_id
            WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
              AND i.remaining_stock <= r.reorder_point
        )
        SELECT
            drug_id,
            drug_name,
            MAX(suggested_reorder_quantity)::INT AS suggested_reorder_quantity,
            MAX(manufacturer_name) AS manufacturer_name,
            MAX(manufacturer_contact) AS manufacturer_contact
        FROM base
        WHERE 1=1
            AND (%s IS NULL OR therapeutic_category = ANY(%s))
            AND (%s IS NULL OR drug_id = ANY(%s))
            AND (%s IS NULL OR drug_name = ANY(%s))
        GROUP BY drug_id, drug_name
        ORDER BY drug_id ASC;
        """

        # Pass None for “no filter”; SQL uses (%s IS NULL OR ...)
        params = [
            therapeutic_categories, therapeutic_categories,
            drug_ids, drug_ids,
            drug_names, drug_names,
        ]

        df = DatabaseManager._read_sql_safe(query, params=params)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_customer_transactions(
        customer_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return transaction history for a given customer."""
        conn = DatabaseManager.get_connection()
        query = """
        SELECT
            dt.transaction_date::DATE AS transaction_date,
            dt.transaction_id,
            d.drug_name,
            d.drug_id,
            dt.quantity,
            dt.unit_price_inr,
            dt.total_value_inr,
            ROUND((dt.quantity * (dt.unit_price_inr - dt.unit_cost_inr))::numeric, 2) AS profit,
            dt.unit_cost_inr AS unit_cost,
            dt.notes
        FROM transactions dt
        LEFT JOIN customers c ON dt.customer_id = c.customer_id
        LEFT JOIN drugs d ON dt.drug_id = d.drug_id
        WHERE dt.transaction_type = 'Sale'
        """

        params = []
        if customer_name:
            query += " AND c.customer_name = %s"
            params.append(customer_name)
        if start_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) >= %s"
            params.append(start_date)
        if end_date is not None:
            query += " AND CAST(dt.transaction_date AS DATE) <= %s"
            params.append(end_date)

        query += " ORDER BY transaction_date DESC, transaction_id DESC;"
        df = DatabaseManager._read_sql_safe(query, params=params if params else None)
        return df

    @staticmethod
    @st.cache_data(ttl=600)
    def get_regular_customers(min_transactions: int = 5, days: Optional[int] = None, customer_names: Optional[List[str]] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Get regular customers with optional date and customer filters."""

        conn = DatabaseManager.get_connection()
        query = """
        SELECT 
            c.customer_id,
            c.customer_name,
            c.city,
            COUNT(DISTINCT dt.transaction_id) as num_transactions,
            COUNT(DISTINCT dt.drug_id) as unique_drugs,
            SUM(dt.total_value_inr) as total_spent,
            ROUND((SUM(dt.total_value_inr) / NULLIF(COUNT(DISTINCT dt.transaction_id), 0))::numeric, 2) as avg_transaction,
            MAX(dt.transaction_date) as last_purchase_date
        FROM customers c
        JOIN transactions dt ON c.customer_id = dt.customer_id
        WHERE dt.transaction_type = 'Sale'
        """

        if days is not None:
            query += f" AND CAST(dt.transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '{int(days)} days'"

        query += """
            AND (%s IS NULL OR c.customer_name = ANY(%s))
            AND (%s IS NULL OR CAST(dt.transaction_date AS DATE) >= %s)
            AND (%s IS NULL OR CAST(dt.transaction_date AS DATE) <= %s)
        GROUP BY c.customer_id, c.customer_name, c.city
        HAVING COUNT(DISTINCT dt.transaction_id) >= %s
        ORDER BY num_transactions DESC;
        """

        params = [
            customer_names, customer_names,
            start_date, start_date,
            end_date, end_date,
            min_transactions,
        ]

        df = DatabaseManager._read_sql_safe(query, params=params)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_bottom_moving_drugs(days: int = 30, limit: int = 5):

        """Get bottom 5 moving drugs by revenue in last N days."""
        conn = DatabaseManager.get_connection()
        query = f"""
        SELECT 
            d.drug_id,
            d.drug_name,
            d.therapeutic_category,
            SUM(dt.quantity) as total_units,
            SUM(dt.total_value_inr) as total_revenue,
            ROUND(
                 (SUM(dt.total_value_inr) / NULLIF({days}, 0))::numeric,
                 2
             ) as avg_daily_revenue,
            a.abc_class
        FROM transactions dt
        JOIN drugs d ON dt.drug_id = d.drug_id
        LEFT JOIN abc_analysis a ON d.drug_id = a.drug_id
        WHERE CAST(dt.transaction_date AS DATE)>= CURRENT_DATE - INTERVAL '{days} days'
          AND dt.transaction_type = 'Sale'
        GROUP BY d.drug_id, d.drug_name, d.therapeutic_category, a.abc_class
        HAVING SUM(dt.total_value_inr) > 0
        ORDER BY total_revenue ASC
        LIMIT {limit};
        """
        df = DatabaseManager._read_sql_safe(query)
        return df
    
    @staticmethod
    @st.cache_data(ttl=300)
    def get_monthly_revenue_metrics():
        """Get last month revenue & MoM growth."""
        conn = DatabaseManager.get_connection()
        query = """
        WITH monthly_revenue AS (
            SELECT 
                DATE_TRUNC(
            'month',
            CAST(dt.transaction_date AS DATE)
                          )::DATE as month,
                SUM(dt.total_value_inr) as total_revenue,
                SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) as total_profit
            FROM transactions dt
            JOIN drugs d ON dt.drug_id = d.drug_id
            WHERE dt.transaction_type = 'Sale'
            GROUP BY month
            ORDER BY month DESC
            LIMIT 2
        )
        SELECT 
            month,
            total_revenue,
            total_profit,
            COALESCE(LAG(total_revenue) OVER (ORDER BY month), total_revenue) as prev_month_revenue
        FROM monthly_revenue
        ORDER BY month DESC;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df
    
    @staticmethod
    @st.cache_data(ttl=300)
    def get_monthly_customer_metrics():
        """Get monthly unique customers & MoM growth."""
        conn = DatabaseManager.get_connection()
        query = """
        WITH monthly_customers AS (
            SELECT 
                DATE_TRUNC('month',CAST(dt.transaction_date AS DATE))::DATE as month,
                COUNT(DISTINCT dt.customer_id) as unique_customers,
                COUNT(DISTINCT dt.transaction_id) as total_transactions
            FROM transactions dt
            WHERE dt.transaction_type = 'Sale'
            GROUP BY month
            ORDER BY month DESC
            LIMIT 2
        )
        SELECT 
            month,
            unique_customers,
            total_transactions,
            COALESCE(LAG(unique_customers) OVER (ORDER BY month), unique_customers) as prev_month_customers
        FROM monthly_customers
        ORDER BY month DESC;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df
    
    @staticmethod
    @st.cache_data(ttl=300)
    def get_profit_trend(days: int = 90):
        """Get daily gross profit trend."""
        conn = DatabaseManager.get_connection()

        query = f"""
        SELECT 
            CAST(dt.transaction_date AS DATE) as date,
            SUM(dt.total_value_inr) as revenue,
            SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) as profit,
            SUM(dt.quantity * d.unit_cost_inr) as cost
        FROM transactions dt
        JOIN drugs d ON dt.drug_id = d.drug_id
        WHERE CAST(dt.transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '{days} days'
          AND dt.transaction_type = 'Sale'
        GROUP BY CAST(dt.transaction_date AS DATE)
        ORDER BY date ASC;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df
    
    # ============== REORDER MANAGEMENT QUERIES ==============
    
    @staticmethod
    @st.cache_data(ttl=300)
    def get_reorder_list():
        """Get all drugs needing reorder (Red status)."""
        conn = DatabaseManager.get_connection()
        query = """
        SELECT
            d.drug_id,
            d.drug_name,
            d.generic_name,
            d.strength,
            i.batch_id,
            i.expiry_date,
            GREATEST((i.expiry_date::date - CURRENT_DATE), 0)::INT AS remaining_days,
            CASE
                WHEN i.expiry_date IS NULL THEN 'Unknown'
                WHEN i.expiry_date < CURRENT_DATE THEN 'Expired'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '30 days' THEN '0-30 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '60 days' THEN '31-60 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '90 days' THEN '61-90 days'
                ELSE 'Safe Stock'
            END AS expiry_bucket,
            i.remaining_stock,
            r.reorder_point,
            r.suggested_reorder_qty,
            r.safety_stock,
            d.manufacturer_name,
            d.manufacturer_phone,
            d.manufacturer_city,
            s.lead_time_days,
            i.snapshot_date
        FROM inventory_snapshots i
        JOIN drugs d ON i.drug_id = d.drug_id
        JOIN reorder_points r ON i.drug_id = r.drug_id
        JOIN lead_times s ON i.drug_id = s.drug_id
        WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
          AND i.stock_status = 'Red'
        ORDER BY i.remaining_stock ASC, i.expiry_date ASC NULLS LAST;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_therapeutic_category_expiry_bins():
        """Get remaining stock counts for each therapeutic category by expiry bucket."""
        conn = DatabaseManager.get_connection()
        query = """
        SELECT
            d.therapeutic_category,
            CASE
                WHEN i.expiry_date IS NULL THEN 'Unknown'
                WHEN i.expiry_date < CURRENT_DATE THEN 'Expired'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '30 days' THEN '0-30 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '60 days' THEN '31-60 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '90 days' THEN '61-90 days'
                ELSE 'Safe Stock'
            END AS expiry_bucket,
            SUM(i.remaining_stock)::INT AS total_qty
        FROM inventory_snapshots i
        JOIN drugs d ON i.drug_id = d.drug_id
        WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
        GROUP BY d.therapeutic_category, expiry_bucket
        ORDER BY d.therapeutic_category, expiry_bucket;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_inventory_stock_status():
        """Get current inventory stock status for all drugs."""
        conn = DatabaseManager.get_connection()
        query = """
        SELECT
            d.drug_id,
            d.drug_name,
            d.generic_name,
            d.therapeutic_category,
            i.stock_status,
            COALESCE(i.remaining_stock, 0)::INT AS remaining_stock,
            COALESCE(r.reorder_point, 0)::INT AS reorder_point,
            COALESCE(r.suggested_reorder_qty, 0)::INT AS suggested_reorder_qty,
            d.manufacturer_name,
            d.manufacturer_phone,
            GREATEST((i.expiry_date::date - CURRENT_DATE), 0)::INT AS remaining_days,
            CASE
                WHEN i.expiry_date IS NULL THEN 'Unknown'
                WHEN i.expiry_date < CURRENT_DATE THEN 'Expired'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '30 days' THEN '0-30 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '60 days' THEN '31-60 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '90 days' THEN '61-90 days'
                ELSE 'Safe Stock'
            END AS expiry_bucket
        FROM inventory_snapshots i
        JOIN drugs d ON i.drug_id = d.drug_id
        LEFT JOIN reorder_points r ON i.drug_id = r.drug_id
        WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
        ORDER BY CASE
            WHEN i.stock_status = 'Red' THEN 1
            WHEN i.stock_status = 'Yellow' THEN 2
            ELSE 3
        END,
        i.remaining_stock ASC;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_expiry_risk_summary():
        """Get expiry risk summary by expiry bucket for current inventory."""
        conn = DatabaseManager.get_connection()
        query = """
        WITH snapshot_data AS (
            SELECT
                i.drug_id,
                i.batch_id,
                i.expiry_date,
                i.remaining_stock,
                COALESCE(d.unit_cost_inr, 0) AS unit_cost_inr,
                CASE
                    WHEN i.expiry_date IS NULL THEN 'Unknown'
                    WHEN i.expiry_date < CURRENT_DATE THEN 'Expired'
                    WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '30 days' THEN '0-30 days'
                    WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '60 days' THEN '31-60 days'
                    WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '90 days' THEN '61-90 days'
                    ELSE 'Safe Stock'
                END AS expiry_bucket
            FROM inventory_snapshots i
            JOIN drugs d ON i.drug_id = d.drug_id
            WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
                AND i.expiry_date IS NOT NULL
        )
        SELECT
            expiry_bucket,
            COUNT(*) AS batch_count,
            COUNT(DISTINCT drug_id) AS distinct_drug_count,
            SUM(remaining_stock) AS total_units,
            ROUND(SUM(remaining_stock * unit_cost_inr)::numeric, 2) AS total_value_inr
        FROM snapshot_data
        GROUP BY expiry_bucket
        ORDER BY
            CASE expiry_bucket
                WHEN 'Expired' THEN 1
                WHEN '0-30 days' THEN 2
                WHEN '31-60 days' THEN 3
                WHEN '61-90 days' THEN 4
                WHEN 'Safe Stock' THEN 5
                ELSE 6
            END;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_expiring_batches(days: int = 60):
        """Get batches that will expire within N days."""
        conn = DatabaseManager.get_connection()
        query = f"""
        SELECT
            d.drug_id,
            d.drug_name,
            d.generic_name,
            d.strength,
            i.batch_id,
            i.expiry_date,
            GREATEST((i.expiry_date::date - CURRENT_DATE), 0)::INT AS remaining_days,
            CASE
                WHEN i.expiry_date < CURRENT_DATE THEN 'Expired'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '30 days' THEN '0-30 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '60 days' THEN '31-60 days'
                WHEN i.expiry_date <= CURRENT_DATE + INTERVAL '90 days' THEN '61-90 days'
                ELSE 'Safe Stock'
            END AS expiry_bucket,
            i.remaining_stock,
            COALESCE(d.unit_cost_inr, 0) AS unit_cost_inr,
            ROUND((i.remaining_stock * COALESCE(d.unit_cost_inr, 0))::numeric, 2) AS expiry_stock_value,
            r.reorder_point,
            r.suggested_reorder_qty,
            r.safety_stock,
            d.manufacturer_name,
            d.manufacturer_phone,
            d.manufacturer_city,
            s.lead_time_days,
            i.snapshot_date
        FROM inventory_snapshots i
        JOIN drugs d ON i.drug_id = d.drug_id
        LEFT JOIN reorder_points r ON i.drug_id = r.drug_id
        LEFT JOIN lead_times s ON i.drug_id = s.drug_id
        WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
            AND i.expiry_date IS NOT NULL
            AND i.expiry_date <= CURRENT_DATE + INTERVAL '{days} days'
        ORDER BY i.expiry_date ASC, i.remaining_stock ASC;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df
    
    # ============== DRUGS INVENTORY QUERIES ==============
    @staticmethod
    @st.cache_data(ttl=300)
    def get_inventory_data():
        """Get complete inventory data for the Drugs Inventory page."""
        conn = DatabaseManager.get_connection()

        query = """
        SELECT
            d.drug_id,
            d.drug_name,
            d.generic_name,
            d.strength,
            d.therapeutic_category,
            d.unit_price_inr,

            i.batch_id,
            i.snapshot_date,
            i.expiry_date,
            i.remaining_stock,
            i.unit_cost_inr,
            i.stock_value_inr,
            i.stock_status,

            r.reorder_point,

            a.abc_class

        FROM inventory_snapshots i

        JOIN drugs d
            ON i.drug_id = d.drug_id

        LEFT JOIN reorder_points r
            ON i.drug_id = r.drug_id

        LEFT JOIN abc_analysis a
            ON i.drug_id = a.drug_id

        WHERE i.snapshot_date = CURRENT_DATE

        ORDER BY
            d.therapeutic_category,
            d.drug_name;
        """

        df = DatabaseManager._read_sql_safe(query)
        return df
    
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_drug_alternatives(generic_name: str):
        """Get all brand alternatives for a generic drug."""
        conn = DatabaseManager.get_connection()
        if conn is None:
            return pd.DataFrame()

        query = """
        SELECT 
            drug_id,
            drug_name,
            generic_name,
            strength,
            dosage_form,
            unit_price_inr,
            unit_cost_inr,
            shelf_life_days,
            manufacturer_name
        FROM drugs
        WHERE generic_name ILIKE %s OR drug_name ILIKE %s
        ORDER BY unit_price_inr DESC;
        """
        pattern = f"%{generic_name}%"
        df = DatabaseManager._read_sql_safe(query, params=[pattern, pattern])
        return df

    @staticmethod
    @st.cache_data(ttl=600)
    def get_drug_lookup():
        """Return all drugs with their IDs, generic names, and strengths."""
        conn = DatabaseManager.get_connection()
        if conn is None:
            return pd.DataFrame()

        query = """
        SELECT
            drug_id,
            drug_name,
            generic_name,
            strength
        FROM drugs
        ORDER BY drug_name;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df

    @staticmethod
    @st.cache_data(ttl=60)
    def search_inventory_by_generic_or_drug_name(search_query: str):
        """Search current inventory by generic name or drug name and return all matching generic family members."""
        conn = DatabaseManager.get_connection()
        if conn is None:
            return pd.DataFrame()

        like_pattern = f"%{search_query}%"
        query = """
        SELECT
            d.generic_name,
            d.drug_id,
            d.drug_name,
            d.strength,
            i.remaining_stock,
            d.unit_price_inr,
            i.expiry_date
        FROM inventory_snapshots i
        JOIN drugs d ON i.drug_id = d.drug_id
        WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
          AND d.generic_name IN (
              SELECT DISTINCT generic_name
              FROM drugs
              WHERE drug_name ILIKE %s OR generic_name ILIKE %s
          )
        ORDER BY d.drug_name, d.strength;
        """
        df = DatabaseManager._read_sql_safe(query, params=[like_pattern, like_pattern])
        return df

    @staticmethod
    def get_latest_batch_id_for_drug_and_date(drug_id: str, snapshot_date: str):
        """Return the most recent batch ID for a drug and snapshot date."""
        conn = DatabaseManager.get_connection()
        if conn is None:
            return None

        query = """
        SELECT batch_id
        FROM inventory_snapshots
        WHERE drug_id = %s
          AND batch_id LIKE %s
        ORDER BY CAST(split_part(batch_id, '-', 3) AS INTEGER) DESC
        LIMIT 1;
        """
        df = DatabaseManager._read_sql_safe(query, params=[drug_id, f"{drug_id}-{snapshot_date}-%"])
        if df.empty:
            return None
        return df.iloc[0, 0]

    @staticmethod
    def insert_inventory_snapshot(
        snapshot_date,
        drug_id: str,
        batch_id: str,
        expiry_date,
        remaining_stock: int,
        unit_cost_inr: float,
        stock_value_inr: float,
    ) -> bool:
        """Insert a new inventory snapshot record with placeholder ETL values."""
        conn = DatabaseManager.get_connection()
        if conn is None:
            raise RuntimeError("Database connection failed.")

        query = """
        INSERT INTO inventory_snapshots (
            snapshot_date,
            drug_id,
            batch_id,
            expiry_date,
            remaining_stock,
            unit_cost_inr,
            stock_value_inr,
            reorder_point,
            safety_stock,
            suggested_reorder_qty,
            stock_status,
            reorder_flag,
            abc_class,
            forecasted_avg_daily_sales,
            is_seasonal,
            seasonality_strength,
            volatility,
            max_stocking_days,
            forecast_method,
            forecast_confidence,
            reorder_explanation,
            qty_explanation
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        params = [
            snapshot_date,
            drug_id,
            batch_id,
            expiry_date,
            remaining_stock,
            unit_cost_inr,
            stock_value_inr,
            0,
            0,
            0,
            'Pending ETL',
            0,
            'Pending',
            0.0,
            False,
            0.0,
            0.0,
            0,
            'Pending',
            0.0,
            '',
            '',
        ]

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise RuntimeError("Failed to insert inventory update. Please try again.") from e
        finally:
            conn.close()
    
    # ============== ABC ANALYSIS QUERIES ==============
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_abc_analysis():
        """Get ABC classification with metrics."""
        conn = DatabaseManager.get_connection()
        query = """
        SELECT 
            a.abc_class,
            COUNT(DISTINCT a.drug_id) as num_drugs,
            ROUND((SUM(a.total_revenue))::numeric, 2) as total_revenue,
            ROUND((SUM(a.total_revenue) /NULLIF((SELECT SUM(total_revenue) FROM abc_analysis),0) * 100)::numeric, 1) as revenue_pct,
            ROUND((AVG(d.shelf_life_days))::numeric, 0) as avg_shelf_life,
            COUNT(CASE WHEN i.stock_status = 'Red' THEN 1 END) as drugs_needing_reorder
        FROM abc_analysis a
        JOIN drugs d ON a.drug_id = d.drug_id
        LEFT JOIN inventory_snapshots i ON a.drug_id = i.drug_id 
            AND i.snapshot_date = CURRENT_DATE
        GROUP BY a.abc_class
        ORDER BY a.abc_class ASC;
        """
        df = DatabaseManager._read_sql_safe(query)
        return df
    
