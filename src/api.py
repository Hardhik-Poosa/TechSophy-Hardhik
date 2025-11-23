"""
FastAPI layer for the TechSophy Finance Insights backend.

Exposes:
    - POST /analyze   : upload CSV, run full pipeline, return summary, recs, figure URLs.
    - GET  /outputs/* : static serving of generated plots and cleaned CSVs.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.logging_config import get_logger
from src.runner import run_pipeline, validate_input_file

logger = get_logger(__name__)

app = FastAPI(title="TechSophy Finance Insights API")

UploadedCSV = Annotated[UploadFile, File(...)]


# ---------------------------------------------------------------------------
# CORS – allow React dev server
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files: serve everything under ./outputs at /outputs
# ---------------------------------------------------------------------------

OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)

app.mount(
    "/outputs",
    StaticFiles(directory=str(OUTPUTS_DIR)),
    name="outputs",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_http_path(path_str: str) -> str:
    """
    Convert a filesystem path like 'outputs/api-runs/123/fig.png'
    into a URL path '/outputs/api-runs/123/fig.png'.
    """
    p = Path(path_str)

    # Make it relative to outputs/ if possible
    try:
        rel = p.relative_to(OUTPUTS_DIR)
    except ValueError:
        # Path is already relative or outside outputs; just use as-is
        rel = p

    return f"/outputs/{rel.as_posix()}"


# ---------------------------------------------------------------------------
# /analyze endpoint
# ---------------------------------------------------------------------------


@app.post("/analyze")
async def analyze_file(
    file: UploadedCSV,
) -> dict[str, Any]:
    """
    Upload a CSV, run the full pipeline, and return summary + recs + figure URLs.

    Response shape:

    {
        "run_id": "...",
        "success": true,
        "summary": { ... },
        "recommendations": [...],
        "figures": {
            "category_spending": "/outputs/api-runs/<run_id>/category_spending.png",
            ...
        },
        "num_anomalies": 3,
        "processed_data_url": "/outputs/api-runs/<run_id>/processed_transactions.csv"
    }
    """
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a CSV file.",
        )

    api_runs_dir = OUTPUTS_DIR / "api-runs"
    api_runs_dir.mkdir(parents=True, exist_ok=True)

    run_id = str(uuid.uuid4())
    run_dir = api_runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    input_path = run_dir / "input.csv"

    # Save uploaded file
    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    # Validate input file quickly (schema / readability)
    if not validate_input_file(str(input_path)):
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV failed basic validation.",
        )

    logger.info("Starting pipeline for run_id=%s", run_id)

    try:
        # Force outputs into run-specific directory
        pipeline_result: dict[str, Any] = run_pipeline(
            csv_path=str(input_path),
            output_dir=str(run_dir),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Pipeline crashed for run_id=%s", run_id)
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal processing error", "error": str(exc)},
        ) from exc

    if not pipeline_result.get("success", False):
        logger.error(
            "Pipeline reported failure for run_id=%s: %s",
            run_id,
            pipeline_result.get("error"),
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Pipeline failed while analyzing the file.",
                "error": pipeline_result.get("error"),
            },
        )

    # ---------------- URL normalisation for frontend ----------------

    raw_figures: dict[str, str] = pipeline_result.get("figures", {}) or {}
    figures_http: dict[str, str] = {
        key: _to_http_path(path_str) for key, path_str in raw_figures.items()
    }

    # Processed CSV: either taken from pipeline_result or computed from run_dir
    processed_path_str = (
        pipeline_result.get("processed_csv_path")
        or pipeline_result.get("processed_path")
        or str(run_dir / "processed_transactions.csv")
    )
    processed_data_url = _to_http_path(processed_path_str)

    summary = pipeline_result.get("summary")
    recommendations = pipeline_result.get("recommendations", [])
    num_anomalies = pipeline_result.get("num_anomalies", 0)

    response: dict[str, Any] = {
        "run_id": run_id,
        "success": True,
        "summary": summary,
        "recommendations": recommendations,
        "figures": figures_http,
        "num_anomalies": num_anomalies,
        "processed_data_url": processed_data_url,
    }

    return response
