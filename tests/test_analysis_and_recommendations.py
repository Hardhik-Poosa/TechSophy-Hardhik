# tests/test_analysis_and_recommendations.py

"""
Tests for src.analysis and src.recommendations modules.

Covers:
- build_analysis_result summary structure
- generate_recommendations returns human readable strings
"""

import pandas as pd

from src.analysis import build_analysis_result
from src.recommendations import generate_recommendations
from src.models import AnalysisSummary, AnalysisResult


def _analysis_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-01-05",
                    "2025-01-10",
                    "2025-02-01",
                    "2025-02-05",
                ]
            ),
            "description": [
                "Starbucks",
                "Uber Trip",
                "Amazon",
                "Netflix Subscription",
                "Apple Store",
            ],
            "amount": [10.0, 20.0, 100.0, 15.99, 2500.0],
            "transaction_type": ["Debit", "Debit", "Debit", "Debit", "Debit"],
            "base_category": [
                "Food",
                "Transport",
                "Shopping",
                "Entertainment",
                "Shopping",
            ],
            "cluster_id": [0, 0, 1, 1, 2],
            "is_anomaly": [False, False, False, False, True],
            "anomaly_score": [-0.1, -0.2, -0.3, -0.4, -5.0],
        }
    )


class TestBuildAnalysisResult:
    def test_summary_structure_and_values(self) -> None:
        df = _analysis_df()
        result = build_analysis_result(df)

        # build_analysis_result returns an AnalysisResult dataclass
        assert isinstance(result, AnalysisResult)

        summary = result.summary
        assert isinstance(summary, AnalysisSummary)

        # Total spend should equal sum of debit amounts
        expected_spend = df["amount"].sum()
        assert summary.total_spend == expected_spend

        # Sanity checks on other fields
        assert summary.total_income >= 0
        assert summary.num_transactions == len(df)

        # Key tables should be DataFrames
        assert isinstance(result.category_stats, pd.DataFrame)
        assert isinstance(result.time_series, pd.DataFrame)
        assert isinstance(result.anomalies, pd.DataFrame)


class TestGenerateRecommendations:
    def test_returns_non_empty_human_readable_list(self) -> None:
        df = _analysis_df()
        analysis_result = build_analysis_result(df)

        recommendations = generate_recommendations(analysis_result)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)

        # At least one recommendation should mention spending or anomalies
        joined = " ".join(recommendations).lower()
        assert "spend" in joined or "anomal" in joined
