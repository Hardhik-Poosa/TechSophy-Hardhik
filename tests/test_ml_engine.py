"""
Tests for src.ml_engine module.

Covers:
- SpendingClusterer basic fit/predict
- AnomalyDetector basic fit/predict
- train_models + apply_models integration
- save_models / load_models round-trip
"""

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from src.ml_engine import (
    SpendingClusterer,
    AnomalyDetector,
    train_models,
    apply_models,
    save_models,
    load_models,
)


def _toy_features() -> pd.DataFrame:
    # Simple 2D feature space with an obvious outlier
    return pd.DataFrame({"amount": [10, 11, 9, 10, 1000], "month": [1, 1, 1, 2, 3]})


def _toy_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03", "2025-02-01", "2025-03-01"]
            ),
            "description": ["A", "B", "C", "D", "E"],
            "amount": [10, 11, 9, 10, 1000],
            "transaction_type": ["Debit"] * 5,
        }
    )


class TestSpendingClusterer:
    def test_fit_and_predict(self) -> None:
        features = _toy_features()
        clusterer = SpendingClusterer(n_clusters=2, random_state=42)

        clusterer.fit(features)
        labels = clusterer.predict(features)

        assert len(labels) == len(features)
        assert set(labels.unique()).issubset({0, 1})


class TestAnomalyDetector:
    def test_detects_outlier(self) -> None:
        features = _toy_features()
        detector = AnomalyDetector(contamination=0.2, random_state=42, n_estimators=50)

        detector.fit(features)
        flags = detector.predict(features)

        # At least one anomaly should be detected
        assert flags.any()


class TestTrainAndApplyModels:
    def test_train_models_and_apply_predictions(self) -> None:
        df = _toy_df()
        features = _toy_features()

        clusterer, detector = train_models(features)
        result_df = apply_models(df, features, clusterer, detector)

        assert "cluster_id" in result_df.columns
        assert "is_anomaly" in result_df.columns
        assert "anomaly_score" in result_df.columns
        assert result_df["is_anomaly"].dtype == bool


class TestModelPersistence:
    def test_save_and_load_models_round_trip(self, tmp_path: Path) -> None:
        features = _toy_features()
        clusterer, detector = train_models(features)

        save_models(clusterer, detector, str(tmp_path))

        loaded_clusterer, loaded_detector = load_models(str(tmp_path))

        # Predictions from loaded models should be of correct length
        labels = loaded_clusterer.predict(features)
        flags = loaded_detector.predict(features)

        assert len(labels) == len(features)
        assert len(flags) == len(features)
        assert flags.dtype == bool


class TestAnomalyScores:
    def test_anomaly_scores_are_finite_and_correlated_with_flags(self) -> None:
        features = _toy_features()
        detector = AnomalyDetector(contamination=0.2, random_state=42, n_estimators=50)

        detector.fit(features)
        scores = detector.score(features)
        flags = detector.predict(features)

        # Length matches and all scores are finite numbers
        assert len(scores) == len(features)
        assert np.isfinite(scores).all()

        # Anomalies should have lower (more "outlier") scores on average
        if flags.any():
            mean_anom = scores[flags].mean()
            mean_normal = scores[~flags].mean()
            assert mean_anom < mean_normal
