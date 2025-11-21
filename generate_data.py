"""
Generate synthetic transaction data for development and testing.

Creates:
    data/input_transactions.csv
    data/input_transactions_with_labels.csv
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import random

import pandas as pd
from faker import Faker

fake = Faker()


def generate_dataset(num_rows: int = 500) -> None:
    start_date = datetime(2025, 1, 1)

    records = []
    labels = []

    spending_profiles = {
        "Food": {
            "descriptions": ["Starbucks", "Local Diner", "McDonalds", "Coffee Shop"],
            "range": (5.0, 40.0),
        },
        "Transport": {
            "descriptions": ["Uber", "Lyft", "City Taxi", "Train Ticket"],
            "range": (8.0, 60.0),
        },
        "Shopping": {
            "descriptions": ["Amazon", "Target", "Mall Store", "Clothing Shop"],
            "range": (20.0, 200.0),
        },
        "Utilities": {
            "descriptions": ["Electric Bill", "Water Bill", "Internet"],
            "range": (50.0, 180.0),
        },
        "Entertainment": {
            "descriptions": ["Netflix", "Spotify", "Movie Theater"],
            "range": (10.0, 80.0),
        },
    }

    for _ in range(num_rows):
        category = random.choice(list(spending_profiles.keys()))
        profile = spending_profiles[category]

        date = start_date + timedelta(days=random.randint(0, 90))
        desc = random.choice(profile["descriptions"])
        amount = round(random.uniform(*profile["range"]), 2)

        records.append(
            {
                "Transaction Date": date.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": amount,
                "Transaction_Type": "Debit",
            }
        )
        labels.append({"Category": category, "Label": "Normal"})

    # recurring Netflix subscription
    for month in range(1, 4):
        date = datetime(2025, month, 15)
        records.append(
            {
                "Transaction Date": date.strftime("%Y-%m-%d"),
                "Description": "Netflix Subscription",
                "Amount": 15.99,
                "Transaction_Type": "Debit",
            }
        )
        labels.append({"Category": "Entertainment", "Label": "Recurring"})

    # one salary deposit per month
    for month in range(1, 4):
        date = datetime(2025, month, 1)
        records.append(
            {
                "Transaction Date": date.strftime("%Y-%m-%d"),
                "Description": "ACH DEPOSIT SALARY",
                "Amount": 3500.00,
                "Transaction_Type": "Credit",
            }
        )
        labels.append({"Category": "Income", "Label": "Normal"})

    # anomalies
    records.append(
        {
            "Transaction Date": "2025-02-10",
            "Description": "Apple Store",
            "Amount": 2500.00,
            "Transaction_Type": "Debit",
        }
    )
    labels.append({"Category": "Shopping", "Label": "Anomaly"})

    records.append(
        {
            "Transaction Date": "2025-03-05",
            "Description": "Unknown Transaction 999",
            "Amount": 1.00,
            "Transaction_Type": "Debit",
        }
    )
    labels.append({"Category": "Other", "Label": "Anomaly"})

    df = pd.DataFrame(records)
    label_df = pd.concat([df, pd.DataFrame(labels)], axis=1)

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(data_dir / "input_transactions.csv", index=False)
    label_df.to_csv(data_dir / "input_transactions_with_labels.csv", index=False)

    print(f"Generated {len(df)} transactions in {data_dir / 'input_transactions.csv'}")


if __name__ == "__main__":
    generate_dataset()
