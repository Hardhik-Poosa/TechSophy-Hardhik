"""
Command-line entry point for the Finance Tracker.

Example:
    python main.py --input data/input_transactions.csv
"""

from __future__ import annotations

import argparse

from src.logging_config import get_logger
from src.runner import run_pipeline, validate_input_file

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personal Finance Tracker")
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input CSV file containing transactions.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Directory to write outputs (defaults to config.yaml data.output_dir).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level).",
    )
    return parser.parse_args()


def _get_summary_value(summary_obj, key: str):
    """
    Helper to read values from either:
    - AnalysisSummary dataclass (attributes), or
    - dict (keys), depending on what runner returns.
    """
    if hasattr(summary_obj, key):
        return getattr(summary_obj, key)
    # fallback for old dict-based version
    return summary_obj[key]


def main() -> None:
    args = parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")

    csv_path = args.input
    if not validate_input_file(csv_path):
        raise SystemExit(1)

    result = run_pipeline(csv_path=csv_path, output_dir=args.output)

    if not result.get("success", False):
        logger.error("Pipeline failed: %s", result.get("error"))
        print(f"Pipeline failed: {result.get('error')}")
        raise SystemExit(1)

    summary = result["summary"]

    total_spend = _get_summary_value(summary, "total_spend")
    total_income = _get_summary_value(summary, "total_income")
    net_cash_flow = _get_summary_value(summary, "net_cash_flow")
    num_transactions = _get_summary_value(summary, "num_transactions")

    num_anomalies = result.get("num_anomalies", 0)

    print("Spending summary")
    print("----------------")
    print(f"Total spending:   {total_spend:.2f}")
    print(f"Total income:     {total_income:.2f}")
    print(f"Net cash flow:    {net_cash_flow:.2f}")
    print(f"Transactions:     {num_transactions}")
    print(f"Anomalies found:  {num_anomalies}")


if __name__ == "__main__":
    main()
