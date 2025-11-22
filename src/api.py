# src/api.py
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.runner import run_pipeline

app = FastAPI(title="TechSophy Finance Insights API")

# Allow local React dev server(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve files under ./outputs at /static/...
app.mount("/static", StaticFiles(directory="outputs"), name="static")

# ---- Ruff B008-safe default for File(...) ----
FILE_PARAM = File(...)  # FastAPI dependency, created once at module level


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TechSophy Finance Insights API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_file(file: UploadFile = FILE_PARAM) -> dict[str, Any]:
    """
    Upload a CSV, run the full pipeline, and return summary + recs + figure URLs.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    # Per-request working directory: outputs/api-runs/<uuid>/
    run_id = str(uuid.uuid4())
    base_output_dir = Path("outputs") / "api-runs" / run_id
    base_output_dir.mkdir(parents=True, exist_ok=True)

    input_path = base_output_dir / "input.csv"
    input_path.write_bytes(await file.read())

    # Use your existing pipeline
    result = run_pipeline(str(input_path), str(base_output_dir))

    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Analysis failed",
                "error_type": result.get("error_type"),
                "error": result.get("error"),
            },
        )

    summary = result["summary"]
    recommendations = result.get("recommendations", [])

    # 🔑 Accept both newer "figures" and your current "figure_paths"
    raw_figures: dict[str, str] = (
        result.get("figures") or result.get("figure_paths") or {}
    )

    # Convert local file paths into URLs under /static/...
    public_figures: dict[str, str] = {}
    for name, path_str in raw_figures.items():
        path = Path(path_str)
        try:
            rel = path.relative_to(Path("outputs"))
        except ValueError:
            # If it's outside ./outputs for some reason, skip it
            continue
        public_figures[name] = f"/static/{rel.as_posix()}"

    return {
        "run_id": run_id,
        "summary": {
            "total_spend": summary.total_spend,
            "total_income": summary.total_income,
            "net_cash_flow": summary.net_cash_flow,
            "num_transactions": summary.num_transactions,
        },
        "recommendations": recommendations,
        # 👇 This is what App.js expects:
        "figures": public_figures,
    }


if __name__ == "__main__":
    import uvicorn

    # Bind only to localhost for local development to satisfy Bandit (B104).
    uvicorn.run(app, host="127.0.0.1", port=8000)
