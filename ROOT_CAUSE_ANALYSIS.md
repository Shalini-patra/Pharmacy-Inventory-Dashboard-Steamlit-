# ROOT CAUSE ANALYSIS - ETL & Dashboard Incompatibilities

---

## ISSUE-BY-ISSUE ROOT CAUSE ANALYSIS

### ISSUE 1: Executive Overview Page - Empty Data
**Symptoms**: "No order activity heatmap data", "No revenue/profit trend data", "No top/bottom moving drug data" 

**Root Causes** (Multiple):
1. **CAST filter inconsistency** - Some queries used `i.snapshot_date = CURRENT_DATE` instead of `CAST(i.snapshot_date AS DATE) = CURRENT_DATE`
   - PostgreSQL type coercion: If snapshot_date is TIMESTAMP, direct DATE comparison fails
   - Returns zero rows even when data exists
   
2. **Impact Chain**: 
   - KPI query returns empty ➜ Dashboard validates and shows error message
   - Revenue query returns empty ➜ Exception raised: "No revenue data available"
   - All dependent visualizations fail

**Root Cause Classification**: Database Query - Type Mismatch

---

### ISSUE 2: Reorder Management Page - No Data
**Symptoms**: "No reorder action rows found for today", "No inventory data found", empty table, KPIs show zero

**Root Causes** (Multiple):
1. **Missing Function**: `get_inventory_heatmap_data()` 
   - Function called in page (line 189) but not implemented in DatabaseManager
   - Filter UI fails to load options
   - Users see empty filter dropdowns
   
2. **CAST Filter Inconsistency**: Same issue as Executive Overview
   - `get_inventory_data()` used `i.snapshot_date = CURRENT_DATE`
   - Returns zero rows
   
3. **Data Chain Failure**: Without filter options → without inventory data → page unusable

**Root Cause Classification**: Missing Implementation + Type Mismatch

---

### ISSUE 3: Transactions & Revenue Page - NaN Conversion Crash
**Symptoms**: "ValueError: cannot convert float NaN to integer"

**Root Cause**: Line 58 in format_axis() function
```python
return f"{int(v)}"  # Crashes if v is NaN
```

**Why NaN exists**:
- Chart axis values can include NaN from financial calculations
- Empty profit values → NaN
- Division by zero → NaN
- Missing data points → NaN

**Execution Flow**:
1. Profit trend query returns data with some NaN values
2. Chart axis calculation produces NaN for missing values
3. format_axis() called on NaN value
4. int(NaN) raises ValueError
5. Page crashes without error boundary

**Root Cause Classification**: Type Safety - Missing NaN Check

---

### ISSUE 4: Drugs Inventory Page - Search Failing
**Symptoms**: "No matching drugs were found for the entered name or generic name"

**Root Cause**: Snapshot date filtering issue
```python
WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
```
If today's snapshot hasn't been generated yet or snapshot_date type is mismatched → no results

**Secondary**: No fallback for historical data or missing snapshots

**Root Cause Classification**: Database Query - Snapshot Availability

---

### ISSUE 5: Customers Analysis Page - No Regular Customers
**Symptoms**: "No regular customer data available for the selected filters"

**Root Cause**: Multiple possibilities
1. Filter logic correctly passes NULL for unselected filters ✓ Working
2. Likely cause: Empty transaction data for the specified date range
3. Or: No customers meet min_transactions threshold (default 5)

**Secondary**: get_regular_customers query is correct, but no graceful empty-state handling

**Root Cause Classification**: Data Availability - Insufficient Data

---

### ISSUE 6: ABC Analysis Page - Metrics Display Errors
**Symptoms**: Page crashes when displaying ABC metrics, RuntimeError on int() calls

**Root Cause**: Multiple unprotected int() conversions
- Line 62: `int(row['num_drugs'])` - Row might have NaN
- Line 82: `int(row['avg_shelf_life'])` - Calculation result can be NaN
- Line 92: `int(row['drugs_needing_reorder'])` - COUNT can be 0, but field might be NaN

**Why NaN Appears**:
- LEFT JOIN with inventory_snapshots produces NULL when no current snapshot
- ROUND() and AVG() can produce NaN with empty groups
- Database casts NULL to NaN in pandas

**Root Cause Classification**: Type Safety - Missing NaN Check

---

### ISSUE 7: Bundle Analysis Page - No Pairs Found
**Symptoms**: "No frequently bought pairs found yet", "More data needed for analysis"

**Root Cause**: Data availability, not code
- Function implementation is correct ✓
- No batch_id filtering issues ✓
- Date filtering is proper ✓
- Likely cause: Insufficient transaction volume in test data
- Or: Historical data doesn't have cross-product transactions in same order

**Secondary**: No informative message about minimum data requirements

**Root Cause Classification**: Data Availability - Insufficient Transaction Volume

---

### ISSUE 8: Duplicate _x/_y Columns in inventory_snapshots
**Symptoms**: Columns like forecasted_avg_daily_sales_x, forecasted_avg_daily_sales_y in database

**Root Cause**: ETL merge operation flaw (incremental_etl.py line 576)
```python
inventory = inventory.drop(
    columns=[...],
    errors='ignore'  # ← PROBLEM: Silently fails
)

inventory = inventory.merge(...)  # ← Creates _x/_y suffixes
```

**Execution Flow**:
1. ETL attempts to drop reorder columns
2. `errors='ignore'` causes silent failure if columns don't exist
3. Columns remain in DataFrame
4. Merge operation finds duplicate column names
5. Pandas creates `column_x` and `column_y` suffixes
6. Both versions stored in database
7. Future queries get confused which version to use

**Why This Happened**:
- Defensive programming with `errors='ignore'` became problematic
- No verification that columns were actually dropped
- No logging to catch the issue

**Root Cause Classification**: ETL Logic - Silent Failure in Data Transformation

---

## ROOT CAUSE SUMMARY BY CATEGORY

### Category 1: Database Query Issues (3 issues)
1. **Inconsistent CAST filter usage** (Executive Overview, Reorder Management, Drugs Inventory)
   - Some queries: `i.snapshot_date = CURRENT_DATE` ✗
   - Some queries: `CAST(i.snapshot_date AS DATE) = CURRENT_DATE` ✓
   - If snapshot_date is TIMESTAMP type → type mismatch → empty results

### Category 2: Type Safety Issues (4 issues)
2. **NaN not handled in integer conversions** (Transactions & Revenue, ABC Analysis, Reorder Management, Bundle Analysis)
   - Pattern: `int(value)` without checking for NaN
   - Source of NaN: Database NULL → pandas NaN, calculations with missing data
   - Fix: Check `pd.isna()` before conversion

### Category 3: Missing Implementation (1 issue)
3. **`get_inventory_heatmap_data()` function not defined** (Reorder Management, Settings)
   - Function called but never implemented
   - Causes filter UI to fail

### Category 4: ETL Data Transformation (1 issue)
4. **Merge operation creates duplicate columns** (incremental_etl.py)
   - Silent failure of `inventory.drop(errors='ignore')`
   - No verification before merge
   - Results in _x/_y suffixes

### Category 5: Data Availability (2 issues - expected behavior)
5. **Insufficient data** (Customers Analysis, Bundle Analysis)
   - Not bugs - expected behavior when data threshold not met
   - Needs better messaging for users

---

## WHY THESE ISSUES APPEARED AFTER ETL REDESIGN

### ETL Schema Changes
1. **TIMESTAMP vs DATE column type change**
   - Old ETL: snapshot_date was DATE type
   - New ETL: snapshot_date now TIMESTAMP type
   - Dashboard queries still assumed DATE type
   - Fix: Use CAST for type safety

2. **Column restructuring in merge operations**
   - Old ETL: Different merge strategy
   - New ETL: Merges reorder_points differently
   - Introduced duplicate columns if old columns existed

3. **Data transformation order changes**
   - ETL pipeline runs transformations in different order
   - Some intermediate tables may be empty
   - Dashboard queries return zero rows

### Dashboard Assumptions Not Updated
1. Queries hardcoded assumptions about column types
2. No type safety checks for NaN values
3. Missing function never added to DatabaseManager
4. No fallback for empty snapshot dates

---

## PREVENTION CHECKLIST FOR FUTURE ETL REDESIGNS

**Before Deployment**:
- [ ] Document all column type changes (DATE → TIMESTAMP)
- [ ] Review all dashboard queries for type assumptions
- [ ] Add CAST for all timestamp comparisons
- [ ] Test all dashboard pages with new schema
- [ ] Verify all functions in DatabaseManager are implemented
- [ ] Check for NaN handling in all integer conversions
- [ ] Add logging to ETL merge operations
- [ ] Verify no duplicate columns created

**After Deployment**:
- [ ] Run full regression test suite
- [ ] Monitor error logs for unexpected type conversions
- [ ] Verify all KPIs display non-zero values
- [ ] Check that all filter dropdowns load correctly

---

## TECHNICAL DEBT ADDRESSED

1. **Type Consistency**: All snapshot_date filters now use CAST
2. **NaN Safety**: All integer conversions protected
3. **Error Transparency**: ETL logging now shows column operations
4. **Function Completeness**: Missing functions added
5. **Merge Robustness**: No more silent failures in data transformation

