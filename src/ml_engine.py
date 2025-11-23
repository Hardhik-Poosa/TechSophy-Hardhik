# src/ml_engine.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

from src.config import get_model_config
from src.logging_config import get_logger
from src.models import ModelError

logger = get_logger(__name__)


# ----------------------------------------------------------
# SpendingClusterer
# ----------------------------------------------------------


@dataclass
class SpendingClusterer:
    n_clusters: int = 5
    random_state: int = 42
    max_iter: int = 300

    model: KMeans | None = field(default=None, init=False)
    is_fitted: bool = field(default=False, init=False)

    def fit(self, features: pd.DataFrame) -> None:
        try:
            logger.info(
                "Fitting KMeans with n_clusters=%s on %s samples",
                self.n_clusters,
                len(features),
            )
            self.model = KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                max_iter=self.max_iter,
                n_init="auto",
            )
            self.model.fit(features)
            self.is_fitted = True
        except Exception as exc:  # pragma: no cover - error path
            raise ModelError(f"Failed to fit cluster model: {exc}") from exc

    def _ensure_fitted(self) -> None:
        if not self.is_fitted or self.model is None:
            raise ModelError("Cluster model has not been fitted yet.")

    def predict(self, features: pd.DataFrame) -> pd.Series:
        self._ensure_fitted()
        try:
            labels = self.model.predict(features)
            return pd.Series(labels, index=features.index)
        except Exception as exc:
            raise ModelError("Failed to predict clusters") from exc

    def get_cluster_profiles(
        self, df: pd.DataFrame, cluster_labels: pd.Series
    ) -> dict[int, dict[str, float]]:
        merged = df.copy()
        merged["cluster_id"] = cluster_labels

        profiles: dict[int, dict[str, float]] = {}

        for cid, group in merged.groupby("cluster_id"):
            profiles[int(cid)] = {
                "count": int(len(group)),
                "avg_amount": float(group["amount"].mean()),
                "min_amount": float(group["amount"].min()),
                "max_amount": float(group["amount"].max()),
            }

        return profiles


# ----------------------------------------------------------
# AnomalyDetector
# ----------------------------------------------------------


@dataclass
class AnomalyDetector:
    contamination: float = 0.05
    random_state: int = 42
    n_estimators: int = 100

    model: IsolationForest | None = field(default=None, init=False)
    is_fitted: bool = field(default=False, init=False)

    def fit(self, features: pd.DataFrame) -> None:
        try:
            logger.info("Fitting IsolationForest on %s samples", len(features))
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=self.n_estimators,
            )
            self.model.fit(features)
            self.is_fitted = True
        except Exception as exc:  # pragma: no cover - error path
            raise ModelError(f"Failed to fit anomaly detector: {exc}") from exc

    def _ensure_fitted(self) -> None:
        """Ensure the underlying IsolationForest model is available and fitted."""
        if not self.is_fitted or self.model is None:
            raise ModelError("Anomaly detector has not been fitted yet.")

    def score(self, features: pd.DataFrame) -> np.ndarray:
        self._ensure_fitted()
        try:
            return self.model.decision_function(features)
        except Exception as exc:
            raise ModelError("Failed to score anomalies") from exc

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        self._ensure_fitted()
        try:
            raw = self.model.predict(features)  # 1 normal, -1 anomaly
            return raw == -1
        except Exception as exc:
            raise ModelError("Failed to predict anomalies") from exc


# ----------------------------------------------------------
# Model training & persistence
# ----------------------------------------------------------


def train_models(features: pd.DataFrame) -> tuple[SpendingClusterer, AnomalyDetector]:
    cfg = get_model_config()
    c_cfg = cfg.get("clustering", {})
    a_cfg = cfg.get("anomaly_detection", {})

    clusterer = SpendingClusterer(
        n_clusters=int(c_cfg.get("n_clusters", 5)),
        random_state=int(c_cfg.get("random_state", 42)),
        max_iter=int(c_cfg.get("max_iter", 300)),
    )

    detector = AnomalyDetector(
        contamination=float(a_cfg.get("contamination", 0.05)),
        random_state=int(a_cfg.get("random_state", 42)),
        n_estimators=int(a_cfg.get("n_estimators", 100)),
    )

    clusterer.fit(features)
    detector.fit(features)

    return clusterer, detector


def apply_models(
    df: pd.DataFrame,
    features: pd.DataFrame,
    clusterer: SpendingClusterer,
    detector: AnomalyDetector,
) -> pd.DataFrame:
    df2 = df.copy()

    df2["cluster_id"] = clusterer.predict(features).values
    df2["anomaly_score"] = detector.score(features)
    df2["is_anomaly"] = detector.predict(features)

    return df2


def save_models(
    clusterer: SpendingClusterer,
    detector: AnomalyDetector,
    model_dir: str,
) -> tuple[str, str]:
    p = Path(model_dir)
    p.mkdir(parents=True, exist_ok=True)

    cluster_path = p / "cluster_model.joblib"
    anomaly_path = p / "anomaly_model.joblib"

    joblib.dump(clusterer, cluster_path)
    joblib.dump(detector, anomaly_path)

    return str(cluster_path), str(anomaly_path)


def load_models(model_dir: str) -> tuple[SpendingClusterer, AnomalyDetector]:
    p = Path(model_dir)

    cluster: SpendingClusterer = joblib.load(p / "cluster_model.joblib")
    detector: AnomalyDetector = joblib.load(p / "anomaly_model.joblib")

    return cluster, detector
