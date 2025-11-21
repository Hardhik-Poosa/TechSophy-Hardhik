# tests/test_ml_engine_exceptions.py

"""
Tests for ML engine exception handling.

These tests deliberately feed invalid inputs to the models to ensure that:
- Low-level scikit-learn exceptions are caught
- They are wrapped into a domain-specific ModelError
- No raw sklearn exceptions leak out of the ML engine
"""

import pandas as pd
import pytest
from src.ml_engine import AnomalyDetector, SpendingClusterer
from src.models import ModelError


class TestSpendingClustererExceptions:
    def test_fit_raises_model_error_on_invalid_features(self) -> None:
        """
        Feeding non-numeric features should cause KMeans.fit to fail.
        The exception must be wrapped into ModelError by the ML engine.
        """
        # Non-numeric feature values
        features = pd.DataFrame({"amount": ["a", "b", "c"]})

        clusterer = SpendingClusterer(n_clusters=3, random_state=42, max_iter=10)

        with pytest.raises(ModelError):
            clusterer.fit(features)


class TestAnomalyDetectorExceptions:
    def test_fit_raises_model_error_on_invalid_features(self) -> None:
        """
        Feeding non-numeric features should cause IsolationForest.fit to fail.
        The exception must be wrapped into ModelError by the ML engine.
        """
        features = pd.DataFrame({"amount": ["x", "y", "z"]})

        detector = AnomalyDetector(contamination=0.1, random_state=42, n_estimators=10)

        with pytest.raises(ModelError):
            detector.fit(features)

    def test_score_and_predict_raise_model_error_if_underlying_model_fails(
        self,
    ) -> None:
        """
        Simulate a corrupted detector state:
        - Mark is_fitted=True but set model=None
        - Any call to score()/predict() should raise ModelError
        """
        features = pd.DataFrame({"amount": [10.0, 20.0, 30.0]})
        detector = AnomalyDetector(contamination=0.1, random_state=42, n_estimators=10)

        # Simulate a previously fitted model that is now invalid
        detector.is_fitted = True
        detector.model = None

        with pytest.raises(ModelError):
            detector.score(features)

        with pytest.raises(ModelError):
            detector.predict(features)
