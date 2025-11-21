"""
Machine Learning engine module.

Implements clustering for spending pattern discovery and
anomaly detection for unusual transaction identification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional  # noqa: F401

import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

from src.config import get_model_config
from src.logging_config import get_logger
from src.models import ClusterProfile, ModelError

logger = get_logger(__name__)


class SpendingClusterer:
    """
    Clustering model for discovering spending patterns using KMeans.
    """

    def __init__(
        self, n_clusters: int = 5, random_state: int = 42, max_iter: int = 300
    ) -> None:
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.max_iter = max_iter
        self.model: KMeans | None = None
        self.is_fitted: bool = False

    def fit(self, features: pd.DataFrame) -> None:
        if features.empty:
            raise ModelError("Cannot fit clustering model on empty feature matrix")

        logger.info("Fitting KMeans with n_clusters=%d", self.n_clusters)
        try:
            self.model = KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                max_iter=self.max_iter,
                n_init=10,
            )
            self.model.fit(features)
            self.is_fitted = True
            logger.info(
                "Clustering completed. Inertia=%.2f", float(self.model.inertia_)
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"Clustering failed: {exc}"
            logger.error(msg)
            raise ModelError(msg) from exc

    def predict(self, features: pd.DataFrame) -> pd.Series:
        if not self.is_fitted or self.model is None:
            raise ModelError("Clusterer must be fitted before prediction")
        try:
            labels = self.model.predict(features)
            return pd.Series(labels, index=features.index)
        except Exception as exc:  # noqa: BLE001
            msg = f"Clustering prediction failed: {exc}"
            logger.error(msg)
            raise ModelError(msg) from exc

    def get_cluster_profiles(
        self, df: pd.DataFrame, cluster_labels: pd.Series
    ) -> list[ClusterProfile]:
        logger.info("Generating cluster profiles")
        profiles: list[ClusterProfile] = []

        df_with_clusters = df.copy()
        df_with_clusters["cluster"] = cluster_labels

        for cluster_id in range(self.n_clusters):
            subset = df_with_clusters[df_with_clusters["cluster"] == cluster_id]
            if subset.empty:
                continue

            top_merchants = (
                subset["description"].value_counts().head(3).index.tolist()
                if "description" in subset.columns
                else []
            )

            dominant_category = None
            if "base_category" in subset.columns and not subset["base_category"].empty:
                dominant_category = subset["base_category"].mode()[0]

            profile = ClusterProfile(
                cluster_id=cluster_id,
                size=int(len(subset)),
                avg_amount=float(subset["amount"].mean()),
                total_amount=float(subset["amount"].sum()),
                top_merchants=top_merchants,
                dominant_category=dominant_category,
            )
            profiles.append(profile)

        logger.info("Generated %d cluster profiles", len(profiles))
        return profiles


class AnomalyDetector:
    """
    Anomaly detection using Isolation Forest.
    """

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
        n_estimators: int = 100,
    ) -> None:
        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.model: IsolationForest | None = None
        self.is_fitted: bool = False

    def fit(self, features: pd.DataFrame) -> None:
        if features.empty:
            raise ModelError("Cannot fit anomaly detector on empty feature matrix")

        logger.info("Fitting Isolation Forest (contamination=%s)", self.contamination)
        try:
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=self.n_estimators,
                n_jobs=-1,
            )
            self.model.fit(features)
            self.is_fitted = True
        except Exception as exc:  # noqa: BLE001
            msg = f"Anomaly detection fitting failed: {exc}"
            logger.error(msg)
            raise ModelError(msg) from exc

    def score(self, features: pd.DataFrame) -> pd.Series:
        if not self.is_fitted or self.model is None:
            raise ModelError("Detector must be fitted before scoring")
        scores = self.model.score_samples(features)
        return pd.Series(scores, index=features.index)

    def predict(self, features: pd.DataFrame) -> pd.Series:
        if not self.is_fitted or self.model is None:
            raise ModelError("Detector must be fitted before prediction")
        preds = self.model.predict(features)
        flags = preds == -1
        return pd.Series(flags, index=features.index)


def train_models(features: pd.DataFrame) -> tuple[SpendingClusterer, AnomalyDetector]:
    """
    Train both clusterer and anomaly detector based on model config.
    """
    cfg = get_model_config()

    clustering_cfg = cfg.get("clustering", {})
    anomaly_cfg = cfg.get("anomaly_detection", {})

    clusterer = SpendingClusterer(
        n_clusters=int(clustering_cfg.get("n_clusters", 5)),
        random_state=int(clustering_cfg.get("random_state", 42)),
        max_iter=int(clustering_cfg.get("max_iter", 300)),
    )
    clusterer.fit(features)

    detector = AnomalyDetector(
        contamination=float(anomaly_cfg.get("contamination", 0.05)),
        random_state=int(anomaly_cfg.get("random_state", 42)),
        n_estimators=int(anomaly_cfg.get("n_estimators", 100)),
    )
    detector.fit(features)

    return clusterer, detector


def apply_models(
    df: pd.DataFrame,
    features: pd.DataFrame,
    clusterer: SpendingClusterer,
    detector: AnomalyDetector,
) -> pd.DataFrame:
    """
    Attach cluster_id, is_anomaly, and anomaly_score to transaction DataFrame.
    """
    df = df.copy()
    df["cluster_id"] = clusterer.predict(features)
    df["is_anomaly"] = detector.predict(features)
    df["anomaly_score"] = detector.score(features)
    return df


def save_models(
    clusterer: SpendingClusterer, detector: AnomalyDetector, path: str
) -> None:
    logger.info("Saving models to %s", path)
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=True)
    joblib.dump(clusterer, folder / "clusterer.pkl")
    joblib.dump(detector, folder / "detector.pkl")


def load_models(path: str) -> tuple[SpendingClusterer, AnomalyDetector]:
    folder = Path(path)
    clusterer = joblib.load(folder / "clusterer.pkl")
    detector = joblib.load(folder / "detector.pkl")
    return clusterer, detector
