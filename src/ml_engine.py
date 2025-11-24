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


# ----------------------------------------------------------
# Human-readable cluster & anomaly explanations
# ----------------------------------------------------------


def describe_clusters(df: pd.DataFrame) -> list[str]:
    """
    df must contain:
      - 'cluster_id' (int)
      - 'amount' (float)
      - 'base_category' (str)  # from preprocessing
      - 'merchant' (str)
    """
    summaries: list[str] = []

    if "cluster_id" not in df.columns:
        logger.warning("describe_clusters: 'cluster_id' column missing")
        return summaries

    for cluster_id, group in df.groupby("cluster_id"):
        if group.empty:
            continue

        mean_amount = group["amount"].mean()
        p25, p75 = np.percentile(group["amount"], [25, 75])

        category_col = "base_category" if "base_category" in group.columns else None
        merchant_col = "merchant" if "merchant" in group.columns else None

        top_categories: list[str] = []
        top_merchants: list[str] = []

        if category_col is not None:
            top_categories = (
                group[category_col].value_counts().head(3).index.astype(str).tolist()
            )

        if merchant_col is not None:
            top_merchants = (
                group[merchant_col].value_counts().head(3).index.astype(str).tolist()
            )

        summary = (
            f"Cluster {cluster_id} represents typical spends around "
            f"₹{p25:,.0f}–₹{p75:,.0f} (avg ₹{mean_amount:,.0f})"
        )

        if top_categories:
            summary += f", mostly in categories: {', '.join(top_categories)}"

        if top_merchants:
            summary += f". Common merchants: {', '.join(top_merchants)}."

        summaries.append(summary)

    return summaries


def describe_top_anomalies(
    df: pd.DataFrame,
    score_col: str = "anomaly_score",
    top_k: int = 10,
) -> list[str]:
    """
    df must contain:
      - score_col (higher = more anomalous)
      - 'date'
      - 'merchant'
      - 'amount'
      - 'base_category'
    """
    if score_col not in df.columns:
        logger.warning("describe_top_anomalies: '%s' column missing", score_col)
        return []

    if df.empty:
        return []

    top = df.sort_values(score_col, ascending=False).head(top_k)

    lines: list[str] = []
    for _, row in top.iterrows():
        date_str = str(row.get("date", "unknown date"))
        merchant = str(row.get("merchant", "unknown merchant"))
        amount = float(row.get("amount", 0.0))
        category = str(row.get("base_category", "Unknown"))

        reason_bits = [f"anomaly score {row[score_col]:.2f}"]

        line = (
            f"On {date_str}, you spent ₹{amount:,.0f} at "
            f"{merchant} (category: {category}) – " + "; ".join(reason_bits) + "."
        )
        lines.append(line)

    return lines


def build_recommendations(df: pd.DataFrame, outputs_dir: Path) -> None:
    """
    Build a human-readable recommendations.txt from cluster + anomaly info.

    Writes:
        outputs_dir / "recommendations.txt"
    """
    outputs_dir.mkdir(parents=True, exist_ok=True)
    recommendations_path = outputs_dir / "recommendations.txt"

    cluster_summaries = describe_clusters(df)
    anomaly_summaries = describe_top_anomalies(df, score_col="anomaly_score", top_k=10)

    lines: list[str] = []

    lines.append("=== Cluster Insights ===")
    lines.append("")
    if cluster_summaries:
        for s in cluster_summaries:
            lines.append(f"- {s}")
    else:
        lines.append("- Could not derive clear cluster patterns from this dataset.")
    lines.append("")

    if anomaly_summaries:
        lines.append("=== Unusual Transactions (Anomalies) ===")
        lines.append("")
        for s in anomaly_summaries:
            lines.append(f"- {s}")
        lines.append("")
    else:
        lines.append("No highly unusual transactions detected in this period.")
        lines.append("")

    # Optionally: flag uncertain categories
    if "is_category_uncertain" in df.columns:
        n_uncertain = int(df["is_category_uncertain"].sum())
        lines.append("=== Category Quality ===")
        lines.append("")
        if n_uncertain > 0:
            lines.append(
                f"- Found {n_uncertain} transactions with low category confidence."
            )
            lines.append(
                "- Please review 'Uncertain' categories manually in the dashboard."
            )
        else:
            lines.append(
                "- All transaction categories are predicted with high confidence."
            )
        lines.append("")

    recommendations_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote recommendations to %s", recommendations_path)
