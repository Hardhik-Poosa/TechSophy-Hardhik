"""
Feature engineering for transaction data.

Responsibilities:
    - Add temporal features
    - Derive high-level spending categories from description
    - Build numeric feature matrix for ML models
    - Scale features
"""

from __future__ import annotations

from typing import Tuple, List

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.logging_config import get_logger

logger = get_logger(__name__)


class PreprocessingService:
    """
    Encapsulates feature engineering logic for reuse and testing.
    """

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add time-based features derived from the 'date' column.
        """
        if "date" not in df.columns:
            raise ValueError("Column 'date' must exist before adding time features")

        logger.debug("Adding time features")

        df = df.copy()
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day
        df["day_of_week"] = df["date"].dt.dayofweek  # Monday=0
        df["year_month"] = df["date"].dt.to_period("M").astype(str)
        return df

    def derive_base_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a coarse-grained 'base_category' from description and type.

        This is a simple rule-based mapping which can later be refined.
        """
        logger.debug("Deriving base categories")

        df = df.copy()
        desc = df["description"].str.lower()

        def classify(row_desc: str) -> str:
            if any(k in row_desc for k in ["uber", "lyft", "cab", "taxi", "train"]):
                return "Transport"
            if any(k in row_desc for k in ["starbucks", "coffee", "restaurant", "diner", "mcdonalds"]):
                return "Food"
            if any(k in row_desc for k in ["netflix", "spotify", "prime video", "subscription"]):
                return "Entertainment"
            if any(k in row_desc for k in ["electric", "water bill", "internet", "utility"]):
                return "Utilities"
            if any(k in row_desc for k in ["amazon", "target", "walmart", "mall", "store"]):
                return "Shopping"
            if any(k in row_desc for k in ["salary", "deposit", "payroll"]):
                return "Income"
            return "Other"

        df["base_category"] = desc.fillna("").apply(classify)
        return df

    def build_feature_matrix(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Build numeric feature matrix for ML models.

        Included features:
            - amount
            - day_of_week
            - month
            - base_category (encoded as ordinal)
        """
        logger.debug("Building feature matrix")

        df = df.copy()

        if "base_category" not in df.columns:
            raise ValueError("Column 'base_category' must exist before building features")

        feature_cols: List[str] = ["amount", "day_of_week", "month"]

        # Encode base_category as ordinal
        category_codes = df["base_category"].astype("category").cat.codes
        df["base_category_code"] = category_codes
        feature_cols.append("base_category_code")

        features = df[feature_cols].astype(float)
        return features, feature_cols

    def scale_features(
        self, features: pd.DataFrame
    ) -> tuple[pd.DataFrame, StandardScaler]:
        """
        Scale numeric features using StandardScaler.
        """
        logger.debug("Scaling feature matrix")
        scaler = StandardScaler()
        scaled_array = scaler.fit_transform(features)
        scaled_df = pd.DataFrame(scaled_array, index=features.index, columns=features.columns)
        return scaled_df, scaler


_default_service = PreprocessingService()


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    return _default_service.add_time_features(df)


def derive_base_category(df: pd.DataFrame) -> pd.DataFrame:
    return _default_service.derive_base_category(df)


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    return _default_service.build_feature_matrix(df)


def scale_features(features: pd.DataFrame) -> tuple[pd.DataFrame, StandardScaler]:
    return _default_service.scale_features(features)
