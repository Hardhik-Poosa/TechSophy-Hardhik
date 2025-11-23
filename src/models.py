# src/models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


class DataValidationError(Exception):
    """Raised when input data fails validation (schema, types, missing columns)."""

    pass


class ModelError(Exception):
    """Raised when ML model operations fail."""

    pass


@dataclass
class AnalysisSummary:
    """High-level numeric summary of the transaction dataset."""

    total_spend: float
    total_income: float
    net_cash_flow: float
    num_transactions: int


@dataclass
class AnalysisResult:
    """
    Container for all analysis artefacts produced by the pipeline.

    Note:
        analysis.build_analysis_result passes:
            - summary
            - category_stats
            - time_series
            - anomalies
            - recurring
            - raw_df
    """

    summary: AnalysisSummary
    category_stats: pd.DataFrame
    time_series: pd.DataFrame
    anomalies: pd.DataFrame

    # New fields used by analysis.py
    recurring: pd.DataFrame | None = None
    raw_df: pd.DataFrame | None = None

    # Optional extra metadata if ever needed
    extra: dict[str, Any] | None = None
