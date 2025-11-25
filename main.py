"""
FastAPI + CLI entrypoint for TechSophy.

- When run with `uvicorn main:app --reload`, this exposes the FastAPI app.
- When run with `python main.py ...`, this runs the CLI pipeline.
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv
from src.api import app as api_app  # existing FastAPI app (with /api routes)
from src.llm_routes import router as llm_router
from src.logging_config import get_logger
from src.runner import run_pipeline, validate_input_file

# Load environment variables from .env (e.g. GEMINI_API_KEY)
load_dotenv()

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app wiring
# ---------------------------------------------------------------------------

# Reuse the FastAPI app defined in src.api
app = api_app

# Attach LLM routes under /api/...
app.include_router(llm_router, prefix="/api")

# Optional: add a simple /health endpoint if not already present in src.api
try:
    from fastapi import APIRouter

    health_router = APIRouter(tags=["health"])

    @health_router.get("/health")
    def health_check():
        return {"status": "ok"}

    app.include_router(health_router)
except Exception:  # pragma: no cover - defensive
    logger.warning("Could not attach health router, but app will still run.")

# ---------------------------------------------------------------------------
# Command-line entry point (same behaviour as your old main.py)
# ---------------------------------------------------------------------------

# Examples:
#
#     python main.py --input data/input_transactions.csv
#     python main.py --train_categories
#


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personal Finance Tracker")

    parser.add_argument(
        "--input",
        "-i",
        default=None,
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
    parser.add_argument(
        "--train_categories",
        action="store_true",
        help="Train the ML category classifier from data/training_categories.csv.",
    )

    args = parser.parse_args()

    # Require --input unless we are only training categories
    if not args.train_categories and args.input is None:
        parser.error("--input is required unless --train_categories is set.")

    return args


def _get_summary_value(summary_obj, key: str):
    """
    Helper to read values from either:
    - AnalysisSummary dataclass (attributes), or
    - dict (keys), depending on what runner returns.
    """
    if hasattr(summary_obj, key):
        return getattr(summary_obj, key)
    return summary_obj[key]


def main() -> None:
    args = parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")
        logger.debug("Verbose logging enabled")

    # Optional training-only mode
    if args.train_categories:
        from src.category_model import train_category_model

        train_category_model("data/training_categories.csv")
        logger.info("Category model training completed.")
        raise SystemExit(0)

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
