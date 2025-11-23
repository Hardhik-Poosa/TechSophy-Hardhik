# src/preprocessing.py
"""
Feature engineering for transaction data.

Responsibilities:
    - Add temporal features
    - Derive high-level spending categories from description (ML + rules)
    - Build numeric feature matrix for ML models
    - Scale features
"""

from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.category_model import CategoryModelNotAvailableError, predict_category
from src.logging_config import get_logger

logger = get_logger(__name__)


class PreprocessingService:
    """Encapsulates feature engineering logic for reuse and testing."""

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features derived from the 'date' column."""
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

    # ---------- Category logic ----------

    @staticmethod
    def _rule_based_category(description: str) -> str:
        """
        Original rule-based fallback for category derivation.
        Kept so behaviour is reasonable even if the ML model is not trained yet.
        """
        text = (description or "").upper()

        if any(
            k in text
            for k in ["ZOMATO", "SWIGGY", "PIZZA", "KFC", "BURGER", "RESTAURANT"]
        ):
            return "Food"
        if any(
            k in text
            for k in ["UBER", "OLA", "RAPIDO", "TRIP", "CAB", "TAXI", "BUS", "METRO"]
        ):
            return "Travel"
        if any(
            k in text for k in ["AMAZON", "FLIPKART", "MYNTRA", "SHOP", "MALL", "DMART"]
        ):
            return "Shopping"
        if any(
            k in text
            for k in ["ELECTRICITY", "WATER BILL", "GAS BILL", "BROADBAND", "RECHARGE"]
        ):
            return "Utilities"
        if any(k in text for k in ["RENT", "HOSTEL FEE", "PG RENT", "ROOM RENT"]):
            return "Rent"
        if any(
            k in text
            for k in ["PVR", "INOX", "NETFLIX", "SPOTIFY", "HOTSTAR", "CINEMA"]
        ):
            return "Entertainment"
        if any(
            k in text
            for k in ["COLLEGE FEE", "TUITION", "COURSE", "EXAM FEE", "LIBRARY"]
        ):
            return "Education"
        if any(
            k in text for k in ["PHARMACY", "HOSPITAL", "CLINIC", "MEDPLUS", "APOLLO"]
        ):
            return "Health"

        return "Other"

    def _safe_predict_category(self, description: str) -> str:
        """
        Try to predict using the ML model. If anything fails (model missing,
        loading error, etc.), fall back to the rule-based category.
        """
        try:
            label = predict_category(description)
            logger.debug("ML category prediction: '%s' -> '%s'", description, label)
            return label
        except CategoryModelNotAvailableError as exc:
            logger.info(
                "Category model not available, falling back to rules: %s",
                exc,
            )
            return self._rule_based_category(description)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Category prediction failed, falling back to rules: %s",
                exc,
            )
            return self._rule_based_category(description)

    def derive_base_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Derive a 'base_category' column using ML classifier when available,
        otherwise fall back to rule-based categorization.
        """
        logger.debug("Deriving base categories (ML + rule-based fallback)")

        if "description" not in df.columns:
            raise ValueError("Expected 'description' column in DataFrame")

        df = df.copy()
        df["base_category"] = (
            df["description"].astype(str).apply(self._safe_predict_category)
        )
        return df

    def build_feature_matrix(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
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
            raise ValueError(
                "Column 'base_category' must exist before building features"
            )

        feature_cols: list[str] = ["amount", "day_of_week", "month"]

        category_codes = df["base_category"].astype("category").cat.codes
        df["base_category_code"] = category_codes
        feature_cols.append("base_category_code")

        features = df[feature_cols].astype(float)
        return features, feature_cols

    def scale_features(
        self, features: pd.DataFrame
    ) -> tuple[pd.DataFrame, StandardScaler]:
        """Scale numeric features using StandardScaler."""
        logger.debug("Scaling feature matrix")
        scaler = StandardScaler()
        scaled_array = scaler.fit_transform(features)
        scaled_df = pd.DataFrame(
            scaled_array, index=features.index, columns=features.columns
        )
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
