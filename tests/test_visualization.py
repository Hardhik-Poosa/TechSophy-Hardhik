# tests/test_visualization.py

"""
Tests for the visualization module.

We do not assert on the visual content of the charts.
Instead, we verify:
- Functions return None when there is no data
- Functions return a valid file path when data is provided
"""

from pathlib import Path

import pandas as pd
from src.visualization import (
    generate_all_plots,
    plot_anomalies,
    plot_category_spend,
    plot_cluster_distribution,
    plot_spend_over_time,
)


def _sample_df_with_predictions() -> pd.DataFrame:
    """
    Construct a small DataFrame resembling the shape after ML models are applied.
    """
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]
            ),
            "amount": [10.0, 20.0, 30.0, 40.0],
            "transaction_type": ["Debit", "Debit", "Debit", "Debit"],
            "is_anomaly": [False, False, True, False],
            "cluster_id": [0, 1, 1, 0],
            "base_category": ["Food", "Transport", "Shopping", "Food"],
        }
    )


def _sample_analysis_result() -> dict[str, object]:
    """
    Build a minimal analysis_result dictionary compatible with generate_all_plots.
    Only the keys used by visualization are populated.
    """
    category_stats = pd.DataFrame(
        {
            "base_category": ["Food", "Transport"],
            "total_amount": [50.0, 70.0],
        }
    )

    time_series = pd.DataFrame(
        {
            "year_month": ["2025-01", "2025-02"],
            "transaction_type": ["Debit", "Debit"],
            "total_amount": [100.0, 150.0],
        }
    )

    # Keys like "summary", "anomalies" etc. are not used by visualization,
    # but we include a minimal structure for completeness.
    return {
        "summary": {
            "total_spend": 120.0,
            "total_income": 0.0,
            "net_cash_flow": -120.0,
            "num_transactions": 4,
        },
        "category_stats": category_stats,
        "time_series": time_series,
        "anomalies": [],
        "by_category": pd.DataFrame(),
        "by_month": pd.DataFrame(),
        "by_weekday": pd.DataFrame(),
        "recurring": pd.DataFrame(),
    }


class TestVisualizationEmptyData:
    def test_category_plot_returns_none_for_empty_data(self, tmp_path: Path) -> None:
        path = plot_category_spend(pd.DataFrame(), str(tmp_path))
        assert path is None

    def test_time_series_plot_returns_none_for_empty_data(self, tmp_path: Path) -> None:
        path = plot_spend_over_time(pd.DataFrame(), str(tmp_path))
        assert path is None

    def test_anomaly_plot_returns_none_when_no_anomaly_column(
        self, tmp_path: Path
    ) -> None:
        df = _sample_df_with_predictions().drop(columns=["is_anomaly"])
        path = plot_anomalies(df, str(tmp_path))
        assert path is None

    def test_cluster_plot_returns_none_when_no_cluster_column(
        self, tmp_path: Path
    ) -> None:
        df = _sample_df_with_predictions().drop(columns=["cluster_id"])
        path = plot_cluster_distribution(df, str(tmp_path))
        assert path is None


class TestVisualizationHappyPath:
    def test_generate_all_plots_creates_files(self, tmp_path: Path) -> None:
        """
        Integration-style test:
        - Use a realistic DataFrame and analysis_result
        - Call generate_all_plots(...)
        - Assert that expected chart files are created
        """
        df = _sample_df_with_predictions()
        analysis_result = _sample_analysis_result()

        figure_paths = generate_all_plots(analysis_result, df, str(tmp_path))

        # At least these plots should be generated
        expected_keys = {
            "category_spending",
            "spending_trends",
            "anomaly_detection",
            "cluster_distribution",
        }

        # All keys must exist
        assert expected_keys.issubset(figure_paths.keys())

        # All referenced files should exist on disk
        for path_str in figure_paths.values():
            assert Path(path_str).exists()
