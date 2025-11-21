"""
Tests for src.preprocessing module.

Covers:
- Time feature engineering
- Base category derivation
- Feature matrix construction
- Feature scaling
"""

import numpy as np
import pandas as pd
from src import preprocessing


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03", "2025-02-10"]
            ),
            "description": ["Starbucks", "Uber Trip", "Amazon Order", "Water Bill"],
            "amount": [12.5, 25.0, 150.0, 80.0],
            "transaction_type": ["Debit", "Debit", "Debit", "Debit"],
        }
    )


class TestAddTimeFeatures:
    def test_adds_expected_columns(self) -> None:
        df = _sample_df()
        result = preprocessing.add_time_features(df)

        for col in ["year", "month", "day", "day_of_week"]:
            assert col in result.columns


class TestDeriveBaseCategory:
    def test_assigns_some_category_labels(self) -> None:
        df = _sample_df()
        result = preprocessing.derive_base_category(df)

        assert "base_category" in result.columns
        # At least one non-null category
        assert result["base_category"].notna().any()


class TestBuildFeatureMatrix:
    def test_feature_matrix_not_empty(self) -> None:
        df = preprocessing.add_time_features(_sample_df())
        df = preprocessing.derive_base_category(df)

        features, feature_cols = preprocessing.build_feature_matrix(df)

        assert not features.empty
        assert len(feature_cols) == features.shape[1]
        # All numeric features
        assert all(np.issubdtype(dt, np.number) for dt in features.dtypes)


class TestScaleFeatures:
    def test_scaling_produces_zero_mean_like_values(self) -> None:
        df = preprocessing.add_time_features(_sample_df())
        df = preprocessing.derive_base_category(df)
        features, _ = preprocessing.build_feature_matrix(df)

        scaled, scaler = preprocessing.scale_features(features)

        assert scaled.shape == features.shape
        # Means should be close to zero after scaling
        assert (scaled.mean().abs() < 1e-6).all()
