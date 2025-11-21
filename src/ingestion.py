"""
Data ingestion and basic cleaning.

Responsibilities:
    - Read CSV from disk
    - Normalize column names
    - Parse dates
    - Handle missing values
    - Validate final schema

Provides both a class-based service and functional helpers for convenience.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from src.config import get_data_config, get_preprocessing_config
from src.logging_config import get_logger
from src.models import DataValidationError

logger = get_logger(__name__)


class TransactionIngestionService:
    """
    Service responsible for loading and validating transaction data.
    """

    def __init__(self, required_columns: Dict[str, str] | None = None) -> None:
        """
        required_columns maps canonical names to possible input variants.
        """
        data_cfg = get_data_config()
        self.required_raw_columns = data_cfg.get("required_columns", [])

        # mapping from canonical -> list of possible patterns
        self.column_aliases: Dict[str, tuple[str, ...]] = required_columns or {
            "date": ("transaction date", "date"),
            "description": ("description", "desc", "details"),
            "amount": ("amount", "transaction amount", "amt"),
            "transaction_type": ("transaction_type", "type", "txn type"),
        }

        self.date_formats = get_preprocessing_config().get("date_formats", [])

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def ingest_transactions(self, csv_path: str | Path) -> pd.DataFrame:
        """
        Execute the full ingestion pipeline.

        Steps:
            1. Load CSV
            2. Normalize columns
            3. Parse dates
            4. Handle missing values
            5. Validate schema
        """
        path = Path(csv_path)
        if not path.exists():
            logger.error("Input CSV file not found: %s", path)
            raise FileNotFoundError(f"CSV file not found at {path}")

        logger.info("Loading transactions from %s", path)
        df = pd.read_csv(path)

        if df.empty:
            raise DataValidationError("Input CSV contains no rows")

        df = self._normalize_columns(df)
        df = self._parse_dates(df)
        df = self._handle_missing_values(df)
        df = self._validate_schema(df)

        logger.info("Ingested %d valid transactions", len(df))
        return df

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to canonical names:
            date, description, amount, transaction_type
        """
        logger.debug("Normalizing column names")
        normalized = {col: col.strip().lower() for col in df.columns}

        mapping: Dict[str, str] = {}
        for canonical, aliases in self.column_aliases.items():
            for col, norm in normalized.items():
                if norm in aliases and canonical not in mapping:
                    mapping[canonical] = col

        missing = [k for k in self.column_aliases.keys() if k not in mapping]
        if missing:
            raise DataValidationError(
                f"Missing required columns (after normalization): {missing}"
            )

        df = df.rename(columns={v: k for k, v in mapping.items()})
        return df

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse date column into datetime.

        Uses pandas automatic parsing with fallbacks to configured formats.
        """
        if "date" not in df.columns:
            raise DataValidationError("Date column not found after normalization")

        logger.debug("Parsing dates")
        # First try pandas automatic parsing
        parsed = pd.to_datetime(df["date"], errors="coerce",)

        if self.date_formats:
            # fill NaT values by trying configured formats
            mask = parsed.isna()
            if mask.any():
                raw_dates = df.loc[mask, "date"]
                for fmt in self.date_formats:
                    try_parsed = pd.to_datetime(
                        raw_dates, errors="coerce", format=fmt
                    )
                    parsed[mask & try_parsed.notna()] = try_parsed[
                        try_parsed.notna()
                    ]

        df["date"] = parsed
        invalid_count = df["date"].isna().sum()
        if invalid_count > 0:
            logger.warning("Dropping %d rows with invalid dates", invalid_count)
            df = df[df["date"].notna()]

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values with safe defaults.
        """
        logger.debug("Handling missing values")

        if "description" in df.columns:
            missing_desc = df["description"].isna().sum()
            if missing_desc:
                logger.warning("Filling %d missing descriptions", missing_desc)
                df["description"] = df["description"].fillna("(no description)")

        if "transaction_type" in df.columns:
            missing_type = df["transaction_type"].isna().sum()
            if missing_type:
                logger.warning("Filling %d missing transaction types", missing_type)
                df["transaction_type"] = df["transaction_type"].fillna("Unknown")

        # Drop rows with missing amounts
        if "amount" not in df.columns:
            raise DataValidationError("Amount column missing after normalization")

        missing_amount = df["amount"].isna().sum()
        if missing_amount:
            logger.warning("Dropping %d rows with missing amounts", missing_amount)
            df = df[df["amount"].notna()]

        return df

    def _validate_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Final schema validation:
            - required columns present
            - correct data types
            - non-empty DataFrame
        """
        logger.debug("Validating schema")

        required = {"date", "description", "amount", "transaction_type"}
        missing = required.difference(df.columns)
        if missing:
            raise DataValidationError(f"Missing required columns: {sorted(missing)}")

        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            raise DataValidationError("Column 'date' is not datetime type")

        if not pd.api.types.is_numeric_dtype(df["amount"]):
            raise DataValidationError("Column 'amount' is not numeric type")

        if df.empty:
            raise DataValidationError("DataFrame is empty after cleaning")

        return df


# Functional façade for tests and convenience -----------------------------


_default_service = TransactionIngestionService()


def ingest_transactions(csv_path: str | Path) -> pd.DataFrame:
    return _default_service.ingest_transactions(csv_path)


# Expose these for unit tests that expect function names
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    return _default_service._normalize_columns(df)


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    return _default_service._parse_dates(df)


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    return _default_service._handle_missing_values(df)


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    return _default_service._validate_schema(df)
