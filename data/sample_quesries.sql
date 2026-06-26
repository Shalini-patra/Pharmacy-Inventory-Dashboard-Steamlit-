-- =============================================================================
-- PHARMACY INVENTORY DASHBOARD - SAMPLE QUERIES
-- 
-- This file contains all important SQL queries used in:
-- 1. ETL Pipeline (data generation & transformation)
-- 2. Streamlit Dashboard (visualization & analytics)
-- 
-- Usage:
-- - Copy individual queries to test in NeonDB
-- - Modify WHERE clauses to filter by specific dates/categories
-- - Use with pandas: pd.read_sql(query, conn)
-- =============================================================================

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 1: EXECUTIVE OVERVIEW QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 1.1: Top Moving Drugs (Last 30 Days)
-- Shows: Top 5 drugs by revenue
SELECT 
    d.drug_id,
    d.drug_name,
    d.therapeutic_category,
    SUM(dt.quantity) as total_units,
    SUM(dt.total_value_inr) as total_revenue,
    ROUND(SUM(dt.total_value_inr) / 30, 2) as avg_daily_revenue,
    a.abc_class
FROM daily_transactions dt
JOIN drugs_details d ON dt.drug_id = d.drug_id
LEFT JOIN abc_analysis a ON d.drug_id = a.drug_id
WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
  AND dt.transaction_type = 'Sale'
GROUP BY d.drug_id, d.drug_name, d.therapeutic_category, a.abc_class
ORDER BY total_revenue DESC
LIMIT 5;

-- Query 1.2: Bottom Moving Drugs (Last 30 Days)
-- Shows: Slowest 5 drugs by revenue
SELECT 
    d.drug_id,
    d.drug_name,
    d.therapeutic_category,
    SUM(dt.quantity) as total_units,
    SUM(dt.total_value_inr) as total_revenue,
    ROUND(SUM(dt.total_value_inr) / 30, 2) as avg_daily_revenue,
    a.abc_class
FROM daily_transactions dt
JOIN drugs_details d ON dt.drug_id = d.drug_id
LEFT JOIN abc_analysis a ON d.drug_id = a.drug_id
WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
  AND dt.transaction_type = 'Sale'
GROUP BY d.drug_id, d.drug_name, d.therapeutic_category, a.abc_class
HAVING SUM(dt.total_value_inr) > 0
ORDER BY total_revenue ASC
LIMIT 5;

-- Query 1.3: Monthly Revenue & Profit Metrics
-- Shows: Current month vs previous month comparison
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', dt.transaction_date)::DATE as month,
        SUM(dt.total_value_inr) as total_revenue,
        SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) as total_profit
    FROM daily_transactions dt
    JOIN drugs_details d ON dt.drug_id = d.drug_id
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

-- Query 1.4: Monthly Customer Metrics
-- Shows: Unique customers this month vs last month
WITH monthly_customers AS (
    SELECT 
        DATE_TRUNC('month', dt.transaction_date)::DATE as month,
        COUNT(DISTINCT dt.customer_id) as unique_customers,
        COUNT(DISTINCT dt.transaction_id) as total_transactions
    FROM daily_transactions dt
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

-- Query 1.5: Daily Profit Trend (Last 90 Days)
-- Shows: Daily revenue, profit, and cost breakdown
SELECT 
    dt.transaction_date::DATE as date,
    SUM(dt.total_value_inr) as revenue,
    SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) as profit,
    SUM(dt.quantity * d.unit_cost_inr) as cost
FROM daily_transactions dt
JOIN drugs_details d ON dt.drug_id = d.drug_id
WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
  AND dt.transaction_type = 'Sale'
GROUP BY dt.transaction_date::DATE
ORDER BY date ASC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 2: REORDER MANAGEMENT QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 2.1: Drugs Needing Reorder (Red Status)
-- Shows: All drugs that have stock < Reorder Point
SELECT 
    d.drug_id,
    d.drug_name,
    d.generic_name,
    d.strength,
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
JOIN drugs_details d ON i.drug_id = d.drug_id
JOIN reorder_calculations r ON i.drug_id = r.drug_id
JOIN supplier_lead_times s ON i.drug_id = s.drug_id
WHERE i.snapshot_date = CURRENT_DATE
  AND i.stock_status = 'Red'
ORDER BY i.remaining_stock ASC;

-- Query 2.2: Drugs Approaching Reorder (Yellow Status)
-- Shows: Drugs in warning zone
SELECT 
    d.drug_id,
    d.drug_name,
    i.remaining_stock,
    r.reorder_point,
    r.suggested_reorder_qty,
    d.manufacturer_name,
    s.lead_time_days
FROM inventory_snapshots i
JOIN drugs_details d ON i.drug_id = d.drug_id
JOIN reorder_calculations r ON i.drug_id = r.drug_id
JOIN supplier_lead_times s ON i.drug_id = s.drug_id
WHERE i.snapshot_date = CURRENT_DATE
  AND i.stock_status = 'Yellow'
ORDER BY i.remaining_stock ASC;

-- Query 2.3: Reorder Summary by Manufacturer
-- Shows: Total reorder quantity needed from each manufacturer
SELECT 
    d.manufacturer_name,
    d.manufacturer_phone,
    d.manufacturer_city,
    COUNT(DISTINCT i.drug_id) as num_drugs_needed,
    SUM(r.suggested_reorder_qty) as total_qty_to_order,
    ROUND(SUM(r.suggested_reorder_qty * d.unit_cost_inr), 2) as estimated_cost
FROM inventory_snapshots i
JOIN drugs_details d ON i.drug_id = d.drug_id
JOIN reorder_calculations r ON i.drug_id = r.drug_id
WHERE i.snapshot_date = CURRENT_DATE
  AND i.stock_status IN ('Red', 'Yellow')
GROUP BY d.manufacturer_name, d.manufacturer_phone, d.manufacturer_city
ORDER BY num_drugs_needed DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 3: INVENTORY & STOCK STATUS QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 3.1: Current Inventory Snapshot (Today)
-- Shows: Stock status for all drugs
SELECT 
    d.drug_id,
    d.drug_name,
    d.generic_name,
    d.therapeutic_category,
    i.remaining_stock,
    i.reorder_point,
    i.stock_status,
    a.abc_class,
    i.avg_daily_sales,
    i.safety_stock,
    i.suggested_reorder_qty
FROM inventory_snapshots i
JOIN drugs_details d ON i.drug_id = d.drug_id
LEFT JOIN abc_analysis a ON i.drug_id = a.drug_id
WHERE i.snapshot_date = CURRENT_DATE
ORDER BY d.therapeutic_category, i.remaining_stock DESC;

-- Query 3.2: Stock Status Distribution
-- Shows: How many drugs in each status (Safe/Yellow/Red)
SELECT 
    stock_status,
    COUNT(*) as num_drugs,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage,
    ROUND(AVG(remaining_stock), 0) as avg_stock_level
FROM inventory_snapshots
WHERE snapshot_date = CURRENT_DATE
GROUP BY stock_status
ORDER BY 
    CASE 
        WHEN stock_status = 'Safe' THEN 1
        WHEN stock_status = 'Yellow' THEN 2
        WHEN stock_status = 'Red' THEN 3
    END;

-- Query 3.3: Inventory Heatmap Data (by Category & Status)
-- Shows: Stock distribution across drug categories
SELECT 
    d.therapeutic_category,
    i.stock_status,
    COUNT(*) as num_drugs,
    ROUND(AVG(i.remaining_stock), 0) as avg_stock,
    ROUND(AVG(i.avg_daily_sales), 2) as avg_daily_sales
FROM inventory_snapshots i
JOIN drugs_details d ON i.drug_id = d.drug_id
WHERE i.snapshot_date = CURRENT_DATE
GROUP BY d.therapeutic_category, i.stock_status
ORDER BY d.therapeutic_category, i.stock_status;

-- Query 3.4: Drug Alternatives (by Generic Name)
-- Shows: All brands of a specific generic drug
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
FROM drugs_details
WHERE generic_name = 'Amoxicillin'  -- MODIFY THIS
ORDER BY unit_price_inr DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 4: ABC ANALYSIS QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 4.1: ABC Classification Summary
-- Shows: Drugs grouped by revenue contribution (A/B/C)
SELECT 
    a.abc_class,
    COUNT(DISTINCT a.drug_id) as num_drugs,
    ROUND(SUM(a.total_revenue), 2) as total_revenue,
    ROUND(SUM(a.total_revenue) / (SELECT SUM(total_revenue) FROM abc_analysis) * 100, 1) as revenue_pct,
    ROUND(AVG(d.shelf_life_days), 0) as avg_shelf_life,
    COUNT(CASE WHEN i.stock_status = 'Red' THEN 1 END) as drugs_needing_reorder
FROM abc_analysis a
JOIN drugs_details d ON a.drug_id = d.drug_id
LEFT JOIN inventory_snapshots i ON a.drug_id = i.drug_id 
    AND i.snapshot_date = CURRENT_DATE
GROUP BY a.abc_class
ORDER BY a.abc_class ASC;

-- Query 4.2: Class A Drugs (Top 20% Revenue)
-- Shows: High-value drugs requiring strict inventory control
SELECT 
    a.drug_id,
    d.drug_name,
    d.generic_name,
    a.total_revenue,
    ROUND(a.total_revenue / (SELECT SUM(total_revenue) FROM abc_analysis) * 100, 2) as revenue_pct,
    i.remaining_stock,
    i.stock_status
FROM abc_analysis a
JOIN drugs_details d ON a.drug_id = d.drug_id
LEFT JOIN inventory_snapshots i ON a.drug_id = i.drug_id 
    AND i.snapshot_date = CURRENT_DATE
WHERE a.abc_class = 'A'
ORDER BY a.total_revenue DESC;

-- Query 4.3: Class C Drugs (Low Value - Simplify Management)
-- Shows: Low-value drugs that can use simplified management
SELECT 
    a.drug_id,
    d.drug_name,
    a.total_revenue,
    COUNT(DISTINCT dt.transaction_id) as num_transactions,
    ROUND(AVG(dt.quantity), 1) as avg_qty_per_sale
FROM abc_analysis a
JOIN drugs_details d ON a.drug_id = d.drug_id
LEFT JOIN daily_transactions dt ON a.drug_id = dt.drug_id 
    AND dt.transaction_type = 'Sale'
    AND dt.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
WHERE a.abc_class = 'C'
GROUP BY a.drug_id, d.drug_name, a.total_revenue
ORDER BY a.total_revenue ASC
LIMIT 20;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 5: CUSTOMER ANALYSIS QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 5.1: Regular Customers (Multiple Transactions in 90 Days)
-- Shows: Loyal customers making 5+ purchases
SELECT 
    c.customer_id,
    c.customer_name,
    c.city,
    c.customer_type,
    COUNT(DISTINCT dt.transaction_id) as num_transactions,
    COUNT(DISTINCT dt.drug_id) as unique_drugs_bought,
    SUM(dt.total_value_inr) as total_spent,
    ROUND(SUM(dt.total_value_inr) / COUNT(DISTINCT dt.transaction_id), 2) as avg_transaction_value,
    MAX(dt.transaction_date) as last_purchase_date,
    ROUND(SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)), 2) as total_profit_generated
FROM customers c
JOIN daily_transactions dt ON c.customer_id = dt.customer_id
JOIN drugs_details d ON dt.drug_id = d.drug_id
WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
  AND dt.transaction_type = 'Sale'
GROUP BY c.customer_id, c.customer_name, c.city, c.customer_type
HAVING COUNT(DISTINCT dt.transaction_id) >= 5
ORDER BY num_transactions DESC;

-- Query 5.2: Customer Churn Analysis
-- Shows: Customers inactive for 30+ days
WITH customer_activity AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.city,
        MAX(dt.transaction_date) as last_purchase,
        COUNT(DISTINCT dt.transaction_id) as total_transactions
    FROM customers c
    LEFT JOIN daily_transactions dt ON c.customer_id = dt.customer_id
    WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY c.customer_id, c.customer_name, c.city
)
SELECT 
    customer_id,
    customer_name,
    city,
    last_purchase,
    CURRENT_DATE - last_purchase::DATE as days_since_purchase,
    total_transactions,
    CASE 
        WHEN last_purchase < CURRENT_DATE - INTERVAL '30 days' THEN 'CHURNED'
        WHEN last_purchase < CURRENT_DATE - INTERVAL '14 days' THEN 'AT RISK'
        ELSE 'ACTIVE'
    END as status
FROM customer_activity
WHERE last_purchase < CURRENT_DATE - INTERVAL '14 days'
ORDER BY days_since_purchase DESC;

-- Query 5.3: New Customers (First Purchase in Last 30 Days)
-- Shows: Newly acquired customers to track retention
SELECT 
    c.customer_id,
    c.customer_name,
    c.city,
    MIN(dt.transaction_date)::DATE as first_purchase_date,
    COUNT(DISTINCT dt.transaction_id) as purchases_since,
    SUM(dt.total_value_inr) as total_value
FROM customers c
JOIN daily_transactions dt ON c.customer_id = dt.customer_id
WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
  AND dt.transaction_type = 'Sale'
GROUP BY c.customer_id, c.customer_name, c.city
HAVING MIN(dt.transaction_date) >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY first_purchase_date DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 6: FINANCIAL IMPACT & LOSS ANALYSIS
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 6.1: Before/After Loss Comparison
-- Shows: Financial benefit of smart dashboard
SELECT 
    period,
    ROUND(total_loss_inr, 2) as total_loss,
    ROUND(stockout_loss_inr, 2) as stockout_loss,
    ROUND(expiry_loss_inr, 2) as expiry_loss,
    stockout_days,
    metric_date
FROM loss_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '180 days'
ORDER BY metric_date DESC
LIMIT 10;

-- Query 6.2: Loss Improvement Metrics
-- Shows: ROI and improvement percentage
SELECT 
    ROUND(loss_reduction_inr, 2) as loss_reduced,
    ROUND(loss_reduction_pct, 2) as improvement_pct,
    ROUND(roi, 2) as roi_multiple,
    metric_date
FROM improvement_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '180 days'
ORDER BY metric_date DESC
LIMIT 1;

-- Query 6.3: Loss by Drug Category
-- Shows: Which drug categories have highest losses
SELECT 
    d.therapeutic_category,
    COUNT(DISTINCT i.drug_id) as num_drugs,
    COUNT(CASE WHEN i.stock_status = 'Red' THEN 1 END) as drugs_out_of_stock,
    ROUND(AVG(i.remaining_stock), 0) as avg_stock_level
FROM inventory_snapshots i
JOIN drugs_details d ON i.drug_id = d.drug_id
WHERE i.snapshot_date = CURRENT_DATE
GROUP BY d.therapeutic_category
ORDER BY drugs_out_of_stock DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 7: BUNDLE ANALYSIS (Frequently Bought Together)
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 7.1: Frequently Bought Together (Top 20 Pairs)
-- Shows: Co-purchase patterns (drugs bought in same transaction)
WITH item_pairs AS (
    SELECT 
        t1.drug_id as drug_1,
        t2.drug_id as drug_2,
        d1.drug_name as drug_1_name,
        d2.drug_name as drug_2_name,
        COUNT(DISTINCT CASE 
            WHEN t1.transaction_id = t2.transaction_id THEN t1.transaction_id 
        END) as co_occurrence_count
    FROM daily_transactions t1
    JOIN daily_transactions t2 
        ON t1.transaction_id = t2.transaction_id 
        AND t1.drug_id < t2.drug_id
    JOIN drugs_details d1 ON t1.drug_id = d1.drug_id
    JOIN drugs_details d2 ON t2.drug_id = d2.drug_id
    WHERE t1.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
      AND t1.transaction_type = 'Sale'
      AND t2.transaction_type = 'Sale'
    GROUP BY t1.drug_id, t2.drug_id, d1.drug_name, d2.drug_name
),
total_transactions AS (
    SELECT COUNT(DISTINCT transaction_id) as total 
    FROM daily_transactions
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '90 days'
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
WHERE co_occurrence_count >= 2
ORDER BY co_occurrence_count DESC
LIMIT 20;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 8: DEMAND FORECASTING & SEASONALITY
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 8.1: Seasonal Drugs Detection
-- Shows: Drugs with seasonal demand patterns
SELECT 
    drug_id,
    COUNT(*) as months_with_data,
    ROUND(AVG(monthly_avg_sales), 2) as annual_avg_sales,
    ROUND(STDDEV(monthly_avg_sales), 2) as sales_std_dev,
    ROUND(STDDEV(monthly_avg_sales) / AVG(monthly_avg_sales), 3) as coefficient_of_variation
FROM (
    SELECT 
        dt.drug_id,
        DATE_TRUNC('month', dt.transaction_date)::DATE as month,
        SUM(dt.quantity) as monthly_avg_sales
    FROM daily_transactions dt
    WHERE dt.transaction_type = 'Sale'
      AND dt.transaction_date >= CURRENT_DATE - INTERVAL '365 days'
    GROUP BY dt.drug_id, DATE_TRUNC('month', dt.transaction_date)
) monthly_data
GROUP BY drug_id
HAVING ROUND(STDDEV(monthly_avg_sales) / AVG(monthly_avg_sales), 3) > 0.15
ORDER BY coefficient_of_variation DESC;

-- Query 8.2: Monthly Sales Pattern for Specific Drug
-- Shows: Seasonal pattern of a specific drug
SELECT 
    EXTRACT(MONTH FROM dt.transaction_date) as month,
    TO_CHAR(dt.transaction_date, 'Month') as month_name,
    SUM(dt.quantity) as total_units,
    ROUND(AVG(dt.quantity), 2) as avg_daily_sales
FROM daily_transactions dt
WHERE dt.drug_id = 'DRG0001'  -- MODIFY THIS
  AND dt.transaction_type = 'Sale'
  AND dt.transaction_date >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY EXTRACT(MONTH FROM dt.transaction_date), TO_CHAR(dt.transaction_date, 'Month')
ORDER BY EXTRACT(MONTH FROM dt.transaction_date);

-- Query 8.3: Forecasted vs Actual Sales (Last 30 Days)
-- Shows: Forecast accuracy
SELECT 
    dt.transaction_date::DATE as date,
    SUM(dt.quantity) as actual_sales,
    r.forecasted_avg_daily_sales * 30 as forecasted_monthly_sales
FROM daily_transactions dt
JOIN drugs_details d ON dt.drug_id = d.drug_id
JOIN reorder_calculations r ON d.drug_id = r.drug_id
WHERE dt.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
  AND dt.transaction_type = 'Sale'
GROUP BY dt.transaction_date::DATE, r.forecasted_avg_daily_sales
ORDER BY date DESC
LIMIT 30;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 9: SUPPLIER & LOGISTICS QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 9.1: Supplier Performance (Lead Time Analysis)
-- Shows: Average lead time by manufacturer
SELECT 
    d.manufacturer_name,
    d.manufacturer_phone,
    COUNT(DISTINCT d.drug_id) as num_drugs,
    ROUND(AVG(s.lead_time_days), 1) as avg_lead_time,
    MIN(s.lead_time_days) as min_lead_time,
    MAX(s.lead_time_days) as max_lead_time
FROM supplier_lead_times s
JOIN drugs_details d ON s.drug_id = d.drug_id
GROUP BY d.manufacturer_name, d.manufacturer_phone
ORDER BY avg_lead_time ASC;

-- Query 9.2: Reorder Cost Analysis (by Manufacturer)
-- Shows: Total cost to order from each supplier
SELECT 
    d.manufacturer_name,
    COUNT(DISTINCT i.drug_id) as num_drugs_to_order,
    SUM(r.suggested_reorder_qty) as total_units,
    ROUND(SUM(r.suggested_reorder_qty * d.unit_cost_inr), 2) as estimated_total_cost,
    ROUND(AVG(s.lead_time_days), 1) as expected_delivery_days
FROM inventory_snapshots i
JOIN drugs_details d ON i.drug_id = d.drug_id
JOIN reorder_calculations r ON i.drug_id = r.drug_id
JOIN supplier_lead_times s ON i.drug_id = s.drug_id
WHERE i.snapshot_date = CURRENT_DATE
  AND i.stock_status IN ('Red', 'Yellow')
GROUP BY d.manufacturer_name
ORDER BY estimated_total_cost DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 10: UTILITY QUERIES (Maintenance & Data Quality)
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 10.1: Data Freshness Check
-- Shows: When was last data update
SELECT 
    'drugs_details' as table_name,
    (SELECT MAX(updated_at) FROM drugs_details) as last_updated,
    (SELECT COUNT(*) FROM drugs_details) as record_count
UNION ALL
SELECT 
    'daily_transactions',
    (SELECT MAX(created_at) FROM daily_transactions),
    (SELECT COUNT(*) FROM daily_transactions)
UNION ALL
SELECT 
    'inventory_snapshots',
    (SELECT MAX(created_at) FROM inventory_snapshots),
    (SELECT COUNT(*) FROM inventory_snapshots)
UNION ALL
SELECT 
    'loss_metrics',
    (SELECT MAX(created_at) FROM loss_metrics),
    (SELECT COUNT(*) FROM loss_metrics)
ORDER BY last_updated DESC;

-- Query 10.2: ETL Pipeline Status
-- Shows: Last successful ETL run details
SELECT 
    etl_run_id,
    run_date,
    stage,
    status,
    records_processed,
    duration_seconds,
    error_message
FROM etl_metadata
ORDER BY run_date DESC
LIMIT 5;

-- Query 10.3: Database Size & Performance
-- Shows: Table sizes and row counts
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    (SELECT COUNT(*) FROM (SELECT * FROM information_schema.tables 
     WHERE table_name = tablename) t) as row_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Query 10.4: Missing Data Check
-- Shows: Drugs with no sales in last 30 days (dead stock)
SELECT 
    d.drug_id,
    d.drug_name,
    d.therapeutic_category,
    COUNT(DISTINCT i.snapshot_date) as days_with_zero_sales,
    ROUND(AVG(i.remaining_stock), 0) as avg_stock_level
FROM drugs_details d
LEFT JOIN inventory_snapshots i ON d.drug_id = i.drug_id
    AND i.snapshot_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN daily_transactions dt ON d.drug_id = dt.drug_id
    AND dt.transaction_type = 'Sale'
    AND dt.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE dt.transaction_id IS NULL
GROUP BY d.drug_id, d.drug_name, d.therapeutic_category
ORDER BY days_with_zero_sales DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- SECTION 11: ADVANCED QUERIES FOR BUSINESS INSIGHTS
-- ═══════════════════════════════════════════════════════════════════════════

-- Query 11.1: Profit Margin Analysis by Category
-- Shows: Which categories are most profitable
SELECT 
    d.therapeutic_category,
    COUNT(DISTINCT d.drug_id) as num_drugs,
    ROUND(AVG(d.margin_pct), 1) as avg_margin_pct,
    SUM(dt.total_value_inr) as total_revenue,
    SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) as total_profit,
    ROUND(SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) / SUM(dt.total_value_inr) * 100, 1) as actual_profit_margin
FROM daily_transactions dt
JOIN drugs_details d ON dt.drug_id = d.drug_id
WHERE dt.transaction_type = 'Sale'
  AND dt.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY d.therapeutic_category
ORDER BY total_profit DESC;

-- Query 11.2: Stock Turnover Rate
-- Shows: How fast inventory is moving (high = good)
SELECT 
    d.drug_id,
    d.drug_name,
    SUM(dt.quantity) as total_sold_90days,
    ROUND(AVG(i.remaining_stock), 0) as avg_stock,
    CASE 
        WHEN AVG(i.remaining_stock) > 0 
        THEN ROUND(SUM(dt.quantity) / AVG(i.remaining_stock) / 90 * 365, 1)
        ELSE 999
    END as annual_turnover_rate
FROM drugs_details d
LEFT JOIN daily_transactions dt ON d.drug_id = dt.drug_id
    AND dt.transaction_type = 'Sale'
    AND dt.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
LEFT JOIN inventory_snapshots i ON d.drug_id = i.drug_id
    AND i.snapshot_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY d.drug_id, d.drug_name
HAVING SUM(dt.quantity) > 0
ORDER BY annual_turnover_rate DESC
LIMIT 20;

-- Query 11.3: Revenue & Profit Contribution by Drug
-- Shows: Top drugs by profit (not just revenue)
SELECT 
    d.drug_id,
    d.drug_name,
    d.therapeutic_category,
    SUM(dt.total_value_inr) as revenue,
    SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) as profit,
    ROUND(SUM(dt.quantity * (d.unit_price_inr - d.unit_cost_inr)) / SUM(dt.total_value_inr) * 100, 1) as profit_margin_pct,
    COUNT(DISTINCT dt.transaction_id) as num_transactions
FROM daily_transactions dt
JOIN drugs_details d ON dt.drug_id = d.drug_id
WHERE dt.transaction_type = 'Sale'
  AND dt.transaction_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY d.drug_id, d.drug_name, d.therapeutic_category
ORDER BY profit DESC
LIMIT 20;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF SAMPLE QUERIES
-- ═══════════════════════════════════════════════════════════════════════════