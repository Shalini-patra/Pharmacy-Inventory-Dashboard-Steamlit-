import pandas as pd
from datetime import datetime, timedelta
from lib.db import DatabaseManager

class AdvancedCalculations:
    """
    Calculations not performed in ETL layer.
    Performed at visualization time for flexibility.
    """
    
    @staticmethod
    def calculate_customer_churn(days_window: int = 90, inactivity_days: int = 30):
        """
        Calculate customer churn rate.
        Churn = customers inactive for X days / total customers in period.
        """
        conn = DatabaseManager.get_connection()
        
        query = f"""
        WITH customer_activity AS (
            SELECT 
                c.customer_id,
                c.customer_name,
                MAX(dt.transaction_date) as last_purchase,
                COUNT(DISTINCT dt.transaction_id) as total_transactions
            FROM customers c
            LEFT JOIN transactions dt ON c.customer_id = dt.customer_id
            WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '{days_window} days'
            GROUP BY c.customer_id, c.customer_name
        )
        SELECT 
            COUNT(CASE WHEN last_purchase < CURRENT_DATE - INTERVAL '{inactivity_days} days' THEN 1 END) as churned_customers,
            COUNT(*) as total_customers,
            ROUND(
                COUNT(CASE WHEN last_purchase < CURRENT_DATE - INTERVAL '{inactivity_days} days' THEN 1 END)::NUMERIC / 
                NULLIF(COUNT(*)::NUMERIC, 0) * 100, 
                2
            ) as churn_rate_pct
        FROM customer_activity;
        """
        
        result = pd.read_sql(query, conn)
        conn.close()
        
        return result.iloc[0].to_dict()
    
    @staticmethod
    def calculate_frequently_bought_together(min_support: float = 0.02):
        """
        Calculate frequently bought together (market basket analysis).
        min_support: minimum % of transactions that must contain both items.
        """
        conn = DatabaseManager.get_connection()
        
        query = f"""
        WITH item_pairs AS (
            SELECT 
                t1.drug_id as drug_1,
                t2.drug_id as drug_2,
                d1.drug_name as drug_1_name,
                d2.drug_name as drug_2_name,
                COUNT(DISTINCT CASE 
                    WHEN t1.transaction_id = t2.transaction_id THEN t1.transaction_id 
                END) as co_occurrence_count
            FROM transactions t1
            JOIN transactions t2 
                ON t1.transaction_id = t2.transaction_id 
                AND t1.drug_id < t2.drug_id  -- Avoid duplicates
            JOIN drugs d1 ON t1.drug_id = d1.drug_id
            JOIN drugs d2 ON t2.drug_id = d2.drug_id
            WHERE CAST(t1.transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
              AND t1.transaction_type = 'Sale'
              AND t2.transaction_type = 'Sale'
            GROUP BY t1.drug_id, t2.drug_id, d1.drug_name, d2.drug_name
        ),
        total_transactions AS (
            SELECT COUNT(DISTINCT transaction_id) as total FROM transactions
            WHERE CAST(transaction_date AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
              AND transaction_type = 'Sale'
        )
        SELECT 
            drug_1,
            drug_2,
            drug_1_name,
            drug_2_name,
            co_occurrence_count,
            ROUND(co_occurrence_count::NUMERIC / (SELECT total FROM total_transactions) * 100, 2) as support_pct
        FROM item_pairs
        WHERE co_occurrence_count >= 2  -- At least 2 co-occurrences
        ORDER BY co_occurrence_count DESC
        LIMIT 20;
        """
        
        result = pd.read_sql(query, conn)
        conn.close()
        
        return result