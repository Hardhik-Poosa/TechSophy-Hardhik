"""FastAPI routes for LLM-powered summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.llm_service import generate_month_summary
from src.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["llm"])


class SummaryRequest(BaseModel):
    """Request body for /api/llm/summary."""

    run_id: str


@router.post("/llm/summary")
async def create_month_summary(payload: SummaryRequest) -> dict[str, Any]:
    """
    Generate an AI-powered monthly summary for a completed pipeline run.

    The frontend passes a `run_id`, which corresponds to an existing
    outputs/api-runs/{run_id}/ directory created by the /analyze endpoint.

    We load processed_transactions.csv, derive a compact payload, and
    delegate to src.llm_service.generate_month_summary().
    """
    run_id = payload.run_id

    base_dir = Path("outputs") / "api-runs" / run_id
    csv_path = base_dir / "processed_transactions.csv"

    logger.info("Loading processed transactions from %s", csv_path)

    if not csv_path.exists():
        msg = f"Processed transactions not found for run_id={run_id}"
        logger.error(msg)
        raise HTTPException(status_code=404, detail=msg)

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to read processed CSV for run_id=%s: %s", run_id, exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to read processed transactions for this run.",
        ) from exc

    # Build a compact payload for the LLM
    num_transactions = int(len(df))

    total_spend = None
    total_income = None
    if "amount" in df.columns:
        # Assuming negative = spend, positive = income
        total_spend = float(df.loc[df["amount"] < 0, "amount"].sum())
        total_income = float(df.loc[df["amount"] > 0, "amount"].sum())

    categories: dict[str, int] = {}
    if "category" in df.columns:
        categories = df["category"].value_counts().to_dict()

    num_anomalies = 0
    if "is_anomaly" in df.columns:
        num_anomalies = int(df["is_anomaly"].sum())

    summary_payload: dict[str, Any] = {
        "run_id": run_id,
        "num_transactions": num_transactions,
        "total_spend": total_spend,
        "total_income": total_income,
        "categories": categories,
        "num_anomalies": num_anomalies,
    }

    try:
        text = generate_month_summary(summary_payload)
        return {"summary": text}
    except Exception as exc:  # pragma: no cover - we want full trace in logs
        logger.error("Failed to generate LLM summary: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
