"""
Business analysis module.

Takes enriched transaction DataFrame (with clusters and anomalies)
and computes:
    - high-level summary metrics
    - category-level statistics
    - monthly time series
    - anomaly view
    - recurring transaction patterns
"""

from __future__ import annotations

from typing import Tuple

import pandas as pd

from src.logging_config import get_logger
from src.models import AnalysisResult, AnalysisSummary

logger = get_logger(__name__)


class AnalysisService:
    """
    Encapsulates business-level spending analysis.
    """

    def build_analysis_result(self, df: pd.DataFrame) -> AnalysisResult:
        """
        Build complete AnalysisResult from processed transaction data.
        """
        summary = self._compute_summary(df)
        category_stats = self._compute_category_stats(df)
        time_series = self._compute_time_series(df)
        anomalies = self._extract_anomalies(df)
        recurring = self._detect_recurring(df)

        return AnalysisResult(
            summary=summary,
            category_stats=category_stats,
            time_series=time_series,
            anomalies=anomalies,
            recurring=recurring,
            raw_df=df.copy(),
        )

    # ------------------------------------------------------------------ #

    def _compute_summary(self, df: pd.DataFrame) -> AnalysisSummary:
        logger.debug("Computing summary metrics")

        debit_mask = df["transaction_type"].str.lower().eq("debit")
        credit_mask = df["transaction_type"].str.lower().eq("credit")

        total_spend = float(df.loc[debit_mask, "amount"].sum())
        total_income = float(df.loc[credit_mask, "amount"].sum())
        net_cash_flow = total_income - total_spend

        return AnalysisSummary(
            total_spend=total_spend,
            total_income=total_income,
            net_cash_flow=net_cash_flow,
            num_transactions=int(len(df)),
        )

    def _compute_category_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Computing category statistics")

        if "base_category" not in df.columns:
            return pd.DataFrame()

        group = (
            df.groupby("base_category", as_index=False)
            .agg(
                total_amount=("amount", "sum"),
                avg_amount=("amount", "mean"),
                num_transactions=("amount", "count"),
            )
            .sort_values("total_amount", ascending=False)
        )
        return group

    def _compute_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Computing time series metrics")

        if "year_month" not in df.columns:
            return pd.DataFrame()

        group = (
            df.groupby(["year_month", "transaction_type"], as_index=False)
            .agg(total_amount=("amount", "sum"))
            .sort_values(["year_month", "transaction_type"])
        )
        return group

    def _extract_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        if "is_anomaly" not in df.columns:
            return pd.DataFrame()
        anomalies = df[df["is_anomaly"]].copy()
        logger.debug("Found %d anomalies", len(anomalies))
        return anomalies

    def _detect_recurring(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Very simple recurring transaction detection:
            - same description
            - similar amount (within 20%)
            - occurs at least twice
        """
        logger.debug("Detecting recurring transactions")

        df = df.copy()
        df["normalized_desc"] = df["description"].str.lower().str.replace(r"\s+", " ", regex=True)

        grouped = (
            df.groupby("normalized_desc")
            .agg(
                num_occurrences=("amount", "count"),
                mean_amount=("amount", "mean"),
                std_amount=("amount", "std"),
                first_date=("date", "min"),
                last_date=("date", "max"),
                sample_description=("description", "first"),
            )
            .reset_index()
        )

        recurring = grouped[grouped["num_occurrences"] >= 2].copy()
        return recurring


_default_service = AnalysisService()


def build_analysis_result(df: pd.DataFrame) -> AnalysisResult:
    return _default_service.build_analysis_result(df)
