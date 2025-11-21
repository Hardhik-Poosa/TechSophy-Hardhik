from __future__ import annotations

from pathlib import Path
from typing import Any

from src.runner import run_pipeline, validate_input_file


def _create_small_input_csv(tmp_path: Path) -> str:
    """
    Create a small but valid CSV file with enough rows so that:
    - KMeans (n_clusters=5) can fit without error
    - Both Debit and Credit transactions exist
    """
    csv_path = tmp_path / "small_transactions.csv"
    csv_path.write_text(
        "Transaction Date,Description,Amount,Transaction_Type\n"
        "2025-01-01,Salary,5000.00,Credit\n"
        "2025-01-02,Coffee,-200.00,Debit\n"
        "2025-01-03,Groceries,-800.00,Debit\n"
        "2025-01-04,Taxi,-300.00,Debit\n"
        "2025-01-05,Shopping,-1200.00,Debit\n"
        "2025-01-06,Subscription,-500.00,Debit\n"
    )
    return str(csv_path)


class TestRunnerIntegration:
    def test_run_pipeline_successful_on_small_csv(self, tmp_path: Path) -> None:
        """
        End-to-end check: run the full pipeline on a small CSV and verify:
        - The pipeline reports success
        - Summary object has sensible values
        - Outputs are written into the given output directory
        """
        csv_path = _create_small_input_csv(tmp_path)
        assert validate_input_file(csv_path) is True

        output_dir = tmp_path / "outputs"
        result: dict[str, Any] = run_pipeline(csv_path, str(output_dir))

        # Success flag
        assert result["success"] is True

        # Summary is a dataclass (AnalysisSummary) with attributes, not a dict
        summary = result["summary"]
        assert summary.total_spend != 0
        assert summary.num_transactions == 6

        # Check that core output files exist
        processed_path = Path(result["processed_data_path"])
        summary_path = Path(result["summary_path"])
        recs_path = Path(result["recommendations_path"])

        assert processed_path.exists()
        assert summary_path.exists()
        assert recs_path.exists()


class TestRunnerErrorHandling:
    def test_run_pipeline_handles_missing_file_gracefully(self, tmp_path: Path) -> None:
        """
        Verify that run_pipeline returns a failure dict when the CSV is missing.
        This covers the error-handling branch in runner.py.
        """
        missing_csv = tmp_path / "does_not_exist.csv"

        result: dict[str, Any] = run_pipeline(
            str(missing_csv), str(tmp_path / "outputs")
        )

        assert result["success"] is False
        assert "error_type" in result
        assert isinstance(result["error"], str)
