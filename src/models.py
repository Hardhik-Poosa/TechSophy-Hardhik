"""
Domain models and custom exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd


# Exceptions ---------------------------------------------------------------


class DataValidationError(Exception):
    """Raised when input data does not meet required schema or quality."""


class ModelError(Exception):
    """Raised when ML model operations fail."""


class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""


# Data classes ------------------------------------------------------------


@dataclass
class ClusterProfile:
    cluster_id: int
    size: int
    avg_amount: float
    total_amount: float
    top_merchants: List[str]
    dominant_category: str | None = None


@dataclass
class AnalysisSummary:
    total_spend: float
    total_income: float
    net_cash_flow: float
    num_transactions: int


@dataclass
class AnalysisResult:
    summary: AnalysisSummary
    category_stats: pd.DataFrame
    time_series: pd.DataFrame
    anomalies: pd.DataFrame
    recurring: pd.DataFrame
    raw_df: pd.DataFrame

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize key metrics to a plain dictionary (for JSON/reporting).
        DataFrames are not fully serialized here, only shapes/basic stats.
        """
        return {
            "summary": {
                "total_spend": self.summary.total_spend,
                "total_income": self.summary.total_income,
                "net_cash_flow": self.summary.net_cash_flow,
                "num_transactions": self.summary.num_transactions,
            },
            "category_stats_rows": len(self.category_stats),
            "time_series_rows": len(self.time_series),
            "num_anomalies": len(self.anomalies),
            "num_recurring": len(self.recurring),
        }
