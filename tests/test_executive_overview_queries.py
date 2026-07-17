import pandas as pd

from lib.executive_overview_queries import apply_executive_overview_filters


def test_apply_executive_overview_filters_counts_distinct_customers():
    df = pd.DataFrame(
        [
            {"transaction_id": 1, "transaction_date": "2024-01-05", "customer_id": 101, "customer_name": "Alice", "drug_id": 1, "drug_name": "Drug A", "therapeutic_category": "Cat A", "quantity": 2, "total_value_inr": 100, "unit_cost_inr": 30, "unit_price_inr": 50},
            {"transaction_id": 2, "transaction_date": "2024-01-10", "customer_id": 101, "customer_name": "Alice", "drug_id": 2, "drug_name": "Drug B", "therapeutic_category": "Cat A", "quantity": 1, "total_value_inr": 80, "unit_cost_inr": 20, "unit_price_inr": 40},
            {"transaction_id": 3, "transaction_date": "2024-02-02", "customer_id": 202, "customer_name": "Bob", "drug_id": 3, "drug_name": "Drug C", "therapeutic_category": "Cat B", "quantity": 3, "total_value_inr": 150, "unit_cost_inr": 25, "unit_price_inr": 55},
        ]
    )

    filtered = apply_executive_overview_filters(
        df,
        {
            "customer_ids": [101],
            "year": 2024,
            "month": 1,
            "start_date": None,
            "end_date": None,
        },
    )

    assert filtered["customer_id"].nunique() == 1
    assert set(filtered["customer_name"].unique()) == {"Alice"}


def test_apply_executive_overview_filters_supports_multiple_filters():
    df = pd.DataFrame(
        [
            {"transaction_id": 1, "transaction_date": "2024-01-05", "customer_id": 101, "customer_name": "Alice", "drug_id": 1, "drug_name": "Drug A", "therapeutic_category": "Cat A", "quantity": 2, "total_value_inr": 100, "unit_cost_inr": 30, "unit_price_inr": 50},
            {"transaction_id": 2, "transaction_date": "2024-01-10", "customer_id": 202, "customer_name": "Bob", "drug_id": 2, "drug_name": "Drug B", "therapeutic_category": "Cat A", "quantity": 1, "total_value_inr": 80, "unit_cost_inr": 20, "unit_price_inr": 40},
            {"transaction_id": 3, "transaction_date": "2023-12-10", "customer_id": 303, "customer_name": "Carol", "drug_id": 3, "drug_name": "Drug C", "therapeutic_category": "Cat B", "quantity": 3, "total_value_inr": 150, "unit_cost_inr": 25, "unit_price_inr": 55},
        ]
    )

    filtered = apply_executive_overview_filters(
        df,
        {
            "customer_ids": [101, 202],
            "year": 2024,
            "month": 1,
            "start_date": None,
            "end_date": None,
        },
    )

    assert filtered.shape[0] == 2
    assert filtered["customer_id"].nunique() == 2
    assert set(filtered["customer_name"].unique()) == {"Alice", "Bob"}
