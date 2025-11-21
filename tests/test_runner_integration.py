# tests/test_runner_integration.py

from pathlib import Path
from typing import Any

import pandas as pd
from src.models import AnalysisSummary
from src.runner import run_pipeline, validate_input_file


def _create_small_input_csv(tmp_path: Path) -> str:
    """
    Create a small but valid CSV file with enough rows
    to satisfy KMeans(n_clusters=5).
    """
    csv_path = tmp_path / "small_transactions.csv"

    df = pd.DataFrame(
        {
            "Transaction Date": [
                "2025-01-01",
                "2025-01-02",
                "2025-01-03",
                "2025-01-04",
                "2025-01-05",
                "2025-01-06",
            ],
            "Description": [
                "Starbucks Store 0032",
                "UBER TRIP 12345",
                "Amazon Purchase",
                "Netflix Subscription",
                "Local Diner",
                "Shell Station",
            ],
            "Amount": [12.50, 35.00, 120.00, 15.99, 20.00, 50.00],
            "Transaction_Type": [
                "Debit",
                "Debit",
                "Debit",
                "Debit",
                "Debit",
                "Debit",
            ],
        }
    )

    df.to_csv(csv_path, index=False)
    return str(csv_path)


class TestRunnerIntegration:
    def test_run_pipeline_successful_on_small_csv(self, tmp_path: Path) -> None:
        """
        End-to-end check: run the full pipeline on a small CSV and verify:
        - The pipeline reports success
        - Summary object has expected attributes
        - Core output files are created
        """
        csv_path = _create_small_input_csv(tmp_path)
        assert validate_input_file(csv_path) is True

        output_dir = tmp_path / "outputs"

        result: dict[str, Any] = run_pipeline(csv_path, str(output_dir))

        # Basic success flag
        assert result["success"] is True

        # Summary should be an AnalysisSummary dataclass
        summary = result["summary"]
        assert isinstance(summary, AnalysisSummary)
        assert summary.total_spend > 0
        assert summary.num_transactions == 6

        # Core output files should exist
        processed = Path(result["processed_data_path"])
        summary_txt = Path(result["summary_path"])
        recs_txt = Path(result["recommendations_path"])

        assert processed.exists()
        assert summary_txt.exists()
        assert recs_txt.exists()

        # At least some figures should be generated
        figure_paths = result["figure_paths"]
        assert isinstance(figure_paths, dict)
        assert "category_spending" in figure_paths
        for path in figure_paths.values():
            assert Path(path).exists()
