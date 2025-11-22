# src/runner.py
"""
Pipeline orchestration module.

Coordinates the complete analysis workflow from raw data to final insights.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src import (
    analysis,
    ingestion,
    ml_engine,
    preprocessing,
    recommendations,
    visualization,
)
from src.config import get_data_config
from src.logging_config import get_logger
from src.models import AnalysisResult, DataValidationError, ModelError

logger = get_logger(__name__)


def run_pipeline(csv_path: str, output_dir: str | None = None) -> dict[str, Any]:
    """
    Execute the complete analysis pipeline.

    Returns:
        Dictionary with summary, recommendations, paths, and metadata.
    """
    logger.info("=" * 50)
    logger.info("Starting Finance Tracker Pipeline")
    logger.info("=" * 50)

    if output_dir is None:
        cfg = get_data_config()
        output_dir = cfg.get("output_dir", "outputs")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # STEP 1: Ingestion
        df = ingestion.ingest_transactions(csv_path)

        # STEP 2: Feature Engineering
        df = preprocessing.add_time_features(df)
        df = preprocessing.derive_base_category(df)
        features, feature_cols = preprocessing.build_feature_matrix(df)
        scaled_features, scaler = preprocessing.scale_features(features)

        # STEP 3: ML Models
        clusterer, detector = ml_engine.train_models(scaled_features)
        df = ml_engine.apply_models(df, scaled_features, clusterer, detector)
        cluster_profiles = clusterer.get_cluster_profiles(df, df["cluster_id"])

        # STEP 4: Analysis
        analysis_result: AnalysisResult = analysis.build_analysis_result(df)

        # STEP 5: Recommendations
        recs = recommendations.generate_recommendations(analysis_result)

        # STEP 6: Visualizations (original 4 charts)
        figure_paths: dict[str, str] = visualization.generate_all_plots(
            {
                "category_stats": analysis_result.category_stats,
                "time_series": analysis_result.time_series,
                "summary": analysis_result.summary,
                "anomalies": analysis_result.anomalies,
            },
            df,
            output_dir,
        )

        # STEP 6b: Advanced visualizations (heatmap, radar, waterfall, forecast)
        # This is optional and must NEVER break the pipeline.
        try:
            advanced_figures = visualization.generate_advanced_plots(
                df,
                output_dir,
                cluster_profiles=cluster_profiles,
            )
            figure_paths.update(advanced_figures)
        except Exception as exc:  # pragma: no cover - best effort only
            logger.warning("Failed to generate advanced plots: %s", exc)

        # STEP 7: Save Outputs
        processed_csv_path = output_path / "processed_transactions.csv"
        df.to_csv(processed_csv_path, index=False)

        recommendations_path = output_path / "recommendations.txt"
        with recommendations_path.open("w", encoding="utf-8") as f:
            for i, rec in enumerate(recs, start=1):
                f.write(f"{i}. {rec}\n\n")

        summary_path = output_path / "summary.txt"
        with summary_path.open("w", encoding="utf-8") as f:
            s = analysis_result.summary
            f.write("SPENDING SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Spending:     {s.total_spend:.2f}\n")
            f.write(f"Total Income:       {s.total_income:.2f}\n")
            f.write(f"Net Cash Flow:      {s.net_cash_flow:.2f}\n")
            f.write(f"Number of Transactions: {s.num_transactions}\n")
            f.write(f"Anomalies Detected:     {len(analysis_result.anomalies)}\n")

        # IMPORTANT:
        # - "figure_paths" kept for tests (existing contract)
        # - "figures" added for API/frontend (same dict)
        result: dict[str, Any] = {
            "success": True,
            "summary": analysis_result.summary,
            "recommendations": recs,
            "figure_paths": figure_paths,
            "figures": figure_paths,
            "processed_data_path": str(processed_csv_path),
            "recommendations_path": str(recommendations_path),
            "summary_path": str(summary_path),
            "num_anomalies": len(analysis_result.anomalies),
            "num_clusters": len(cluster_profiles),
            "cluster_profiles": cluster_profiles,
        }

        logger.info("Pipeline completed successfully")
        return result

    except DataValidationError as exc:
        logger.error("Data validation failed: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "error_type": "DataValidationError",
        }
    except ModelError as exc:
        logger.error("Model error: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "error_type": "ModelError",
        }
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Unexpected error in pipeline: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": str(exc),
            "error_type": "UnexpectedError",
        }


def validate_input_file(csv_path: str) -> bool:
    """
    Validate that input file exists and is accessible.
    """
    path = Path(csv_path)

    if not path.exists():
        logger.error("Input file does not exist: %s", csv_path)
        return False

    if not path.is_file():
        logger.error("Input path is not a file: %s", csv_path)
        return False

    if path.suffix.lower() != ".csv":
        logger.warning("Input file does not have .csv extension: %s", csv_path)

    return True
