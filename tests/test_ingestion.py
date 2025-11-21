"""
Tests for src.ingestion module.

Covers:
- Column normalization
- Date parsing
- Missing value handling
- Schema validation
- End-to-end ingest_transactions on a temp CSV
"""

from pathlib import Path
from datetime import datetime

import pandas as pd
import pytest

from src.ingestion import (
    normalize_columns,
    parse_dates,
    handle_missing_values,
    validate_schema,
    ingest_transactions,
)
from src.models import DataValidationError


class TestNormalizeColumns:
    def test_normalize_standard_column_names(self) -> None:
        df = pd.DataFrame(
            {
                "Transaction Date": ["2025-01-01"],
                "Description": ["Test"],
                "Amount": [100.0],
                "Transaction_Type": ["Debit"],
            }
        )

        result = normalize_columns(df)

        assert set({"date", "description", "amount", "transaction_type"}).issubset(
            result.columns
        )

    def test_normalize_alternative_column_names(self) -> None:
        df = pd.DataFrame(
            {
                "Date": ["2025-01-01"],
                "Desc": ["Test"],
                "Transaction Amount": [100.0],
                "Type": ["Debit"],
            }
        )

        result = normalize_columns(df)

        assert "date" in result.columns
        assert "description" in result.columns
        assert "amount" in result.columns
        assert "transaction_type" in result.columns

    def test_normalize_is_case_insensitive(self) -> None:
        df = pd.DataFrame(
            {
                "TRANSACTION DATE": ["2025-01-01"],
                "DESCRIPTION": ["Test"],
                "AMOUNT": [100.0],
                "TRANSACTION_TYPE": ["Debit"],
            }
        )

        result = normalize_columns(df)

        assert "date" in result.columns
        assert "description" in result.columns
        assert "amount" in result.columns
        assert "transaction_type" in result.columns


class TestParseDates:
    def test_parse_iso_format(self) -> None:
        df = pd.DataFrame({"date": ["2025-01-15", "2025-02-20", "2025-03-10"]})

        result = parse_dates(df)

        assert pd.api.types.is_datetime64_any_dtype(result["date"])
        assert result["date"].notna().all()

    def test_parse_mixed_formats(self) -> None:
        """Test parsing dates in multiple formats."""
        df = pd.DataFrame(
            {"date": ["2025-01-15", "15/02/2025", "Mar 10, 2025", "invalid-date"]}
        )

        result = parse_dates(df)

        # Invalid rows should be removed and remaining dates all valid
        assert len(result) < len(df)
        assert pd.api.types.is_datetime64_any_dtype(result["date"])
        assert result["date"].notna().all()
    def test_missing_date_column_raises(self) -> None:
        df = pd.DataFrame({"description": ["Test"]})

        with pytest.raises(DataValidationError):
            parse_dates(df)


class TestHandleMissingValues:
    def test_fill_missing_description_and_type(self) -> None:
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
                "description": ["Coffee", None],
                "amount": [10.0, 20.0],
                "transaction_type": ["Debit", None],
            }
        )

        result = handle_missing_values(df)

        assert result["description"].isna().sum() == 0
        assert result["transaction_type"].isna().sum() == 0

    def test_drop_rows_with_missing_amount(self) -> None:
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
                "description": ["A", "B", "C"],
                "amount": [10.0, None, 30.0],
                "transaction_type": ["Debit", "Debit", "Debit"],
            }
        )

        result = handle_missing_values(df)

        assert len(result) == 2
        assert result["amount"].notna().all()


class TestValidateSchema:
    def test_valid_schema_passes(self) -> None:
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
                "description": ["A", "B"],
                "amount": [10.0, 20.0],
                "transaction_type": ["Debit", "Credit"],
            }
        )

        validated = validate_schema(df)
        assert isinstance(validated, pd.DataFrame)

    def test_missing_required_columns_raises(self) -> None:
        df = pd.DataFrame({"date": pd.to_datetime(["2025-01-01"]), "description": ["A"]})

        with pytest.raises(DataValidationError):
            validate_schema(df)

    def test_non_datetime_date_raises(self) -> None:
        df = pd.DataFrame(
            {
                "date": ["2025-01-01"],
                "description": ["A"],
                "amount": [10.0],
                "transaction_type": ["Debit"],
            }
        )

        with pytest.raises(DataValidationError):
            validate_schema(df)

    def test_non_numeric_amount_raises(self) -> None:
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-01"]),
                "description": ["A"],
                "amount": ["ten"],  # invalid
                "transaction_type": ["Debit"],
            }
        )

        with pytest.raises(DataValidationError):
            validate_schema(df)


class TestIngestTransactionsIntegration:
    def test_ingest_valid_csv_round_trip(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "transactions.csv"
        csv_path.write_text(
            "Transaction Date,Description,Amount,Transaction_Type\n"
            "2025-01-15,Starbucks,12.50,Debit\n"
            "2025-01-20,Salary,3500.00,Credit\n"
        )

        df = ingest_transactions(str(csv_path))

        assert len(df) == 2
        assert set({"date", "description", "amount", "transaction_type"}).issubset(
            df.columns
        )
        assert df["amount"].sum() == pytest.approx(3512.50)

    def test_ingest_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            ingest_transactions("does_not_exist.csv")
