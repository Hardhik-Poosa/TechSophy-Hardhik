# src/visualization.py

"""
Visualization module.

Generates charts and graphs for spending analysis.
Saves publication-quality figures to disk.
"""

import logging
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import get_visualization_config
from src.logging_config import get_logger

# ---- Safe backend configuration (flake8-compatible) ----
try:
    matplotlib.use("Agg", force=True)
except Exception as exc:  # noqa: BLE001
    logging.getLogger(__name__).warning(
        "Could not set matplotlib backend to Agg: %s", exc
    )
# Suppress matplotlib warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

logger = get_logger(__name__)


def _setup_plot_style() -> None:
    """Configure consistent matplotlib/seaborn style."""
    config = get_visualization_config()
    style = config.get("style", "seaborn-v0_8-darkgrid")

    try:
        plt.style.use(style)
    except Exception:
        sns.set_theme()

    sns.set_palette("husl")


def _save_figure(fig: plt.Figure, output_path: str) -> str:
    """Save figure to disk with configured DPI and format."""
    config = get_visualization_config()
    dpi = config.get("dpi", 100)
    output_format = config.get("output_format", "png")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, format=output_format, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"Saved figure to: {output_path}")
    return str(output_file.absolute())


def plot_category_spend(category_stats: pd.DataFrame, output_dir: str) -> str | None:
    """Bar chart of spending by category."""
    logger.info("Generating category spending chart")

    if category_stats.empty:
        logger.warning("No category data to plot")
        return None

    _setup_plot_style()
    figsize = tuple(get_visualization_config().get("figure_size", [10, 6]))
    fig, ax = plt.subplots(figsize=figsize)

    sns.barplot(
        data=category_stats.head(10),
        y="base_category",
        x="total_amount",
        ax=ax,
        palette="viridis",
    )

    ax.set_xlabel("Total Spending ($)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Category", fontsize=12, fontweight="bold")
    ax.set_title("Spending by Category", fontsize=14, fontweight="bold")

    for container in ax.containers:
        ax.bar_label(container, fmt="$%.0f")

    return _save_figure(fig, str(Path(output_dir) / "category_spending.png"))


def plot_spend_over_time(time_series: pd.DataFrame, output_dir: str) -> str | None:
    """Create line chart of spending trends over time."""
    logger.info("Generating time series chart")

    if time_series.empty:
        logger.warning("No time series data to plot")
        return None

    _setup_plot_style()
    figsize = tuple(get_visualization_config().get("figure_size", [10, 6]))
    fig, ax = plt.subplots(figsize=figsize)

    for txn_type in time_series["transaction_type"].unique():
        data = time_series.loc[time_series["transaction_type"] == txn_type]
        ax.plot(
            data["year_month"],
            data["total_amount"],
            marker="o",
            linewidth=2,
            label=txn_type,
        )

    ax.set_xlabel("Month", fontsize=12, fontweight="bold")
    ax.set_ylabel("Amount ($)", fontsize=12, fontweight="bold")
    ax.set_title("Spending Trends Over Time", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45, ha="right")

    return _save_figure(fig, str(Path(output_dir) / "spending_trends.png"))


def plot_anomalies(df: pd.DataFrame, output_dir: str) -> str | None:
    """Scatter plot for anomalies."""
    logger.info("Generating anomaly visualization")

    if "is_anomaly" not in df.columns:
        logger.warning("No anomaly data to plot")
        return None

    _setup_plot_style()
    figsize = tuple(get_visualization_config().get("figure_size", [12, 6]))
    fig, ax = plt.subplots(figsize=figsize)

    # Normal vs anomalous
    normal = df.loc[~df["is_anomaly"]]
    anomalies = df.loc[df["is_anomaly"]]

    ax.scatter(
        normal["date"],
        normal["amount"],
        alpha=0.5,
        s=50,
        c="blue",
        label="Normal",
    )

    if not anomalies.empty:
        ax.scatter(
            anomalies["date"],
            anomalies["amount"],
            alpha=0.8,
            s=150,
            c="red",
            marker="X",
            edgecolors="black",
            linewidths=1.5,
            label="Anomaly",
        )

    ax.set_xlabel("Date", fontsize=12, fontweight="bold")
    ax.set_ylabel("Amount ($)", fontsize=12, fontweight="bold")
    ax.set_title("Transaction Anomalies", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45, ha="right")

    return _save_figure(fig, str(Path(output_dir) / "anomaly_detection.png"))


def plot_cluster_distribution(df: pd.DataFrame, output_dir: str) -> str | None:
    """Boxplot of spending clusters."""
    logger.info("Generating cluster distribution chart")

    if "cluster_id" not in df.columns:
        logger.warning("No cluster data to plot")
        return None

    _setup_plot_style()
    figsize = tuple(get_visualization_config().get("figure_size", [10, 6]))
    fig, ax = plt.subplots(figsize=figsize)

    df_debit = df.loc[df["transaction_type"] == "Debit"]

    sns.boxplot(
        data=df_debit,
        x="cluster_id",
        y="amount",
        ax=ax,
        palette="Set2",
    )

    ax.set_xlabel("Cluster ID", fontsize=12, fontweight="bold")
    ax.set_ylabel("Transaction Amount ($)", fontsize=12, fontweight="bold")
    ax.set_title("Spending Patterns by Cluster", fontsize=14, fontweight="bold")

    return _save_figure(fig, str(Path(output_dir) / "cluster_distribution.png"))


def generate_all_plots(
    analysis_result: dict, df: pd.DataFrame, output_dir: str
) -> dict[str, str]:
    """Generate all charts and return mapping of chart_name → filepath."""
    logger.info(f"Generating all plots in directory: {output_dir}")

    figure_paths: dict[str, str] = {}

    category_stats = analysis_result.get("category_stats", pd.DataFrame())
    if p := plot_category_spend(category_stats, output_dir):
        figure_paths["category_spending"] = p

    time_series = analysis_result.get("time_series", pd.DataFrame())
    if p := plot_spend_over_time(time_series, output_dir):
        figure_paths["spending_trends"] = p

    if p := plot_anomalies(df, output_dir):
        figure_paths["anomaly_detection"] = p

    if p := plot_cluster_distribution(df, output_dir):
        figure_paths["cluster_distribution"] = p

    logger.info(f"Generated {len(figure_paths)} visualization(s)")
    return figure_paths


# --- Advanced visualizations: heatmap, radar, waterfall, forecast ---


def generate_correlation_heatmap(
    df: pd.DataFrame,
    output_dir: Path,
) -> str | None:
    """
    Correlation heatmap of numeric columns.
    Returns output file path or None if not enough numeric data.
    """
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty or numeric_df.shape[1] < 2:
        logger.info("Skipping heatmap: not enough numeric columns.")
        return None

    corr = numeric_df.corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="viridis",
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Feature Correlation Heatmap", fontsize=14)
    fig.tight_layout()

    output_path = Path(output_dir) / "correlation_heatmap.png"
    fig.savefig(output_path)
    plt.close(fig)
    logger.info("Saved heatmap to: %s", output_path)
    return str(output_path)


def generate_cluster_radar_chart(
    cluster_profiles: dict[int, dict[str, float]] | None,
    output_dir: Path,
) -> str | None:
    """
    Radar chart of cluster profiles (avg/min/max amount + count).
    Expects the dict returned by SpendingClusterer.get_cluster_profiles().
    """
    if not cluster_profiles:
        logger.info("Skipping radar chart: empty cluster_profiles.")
        return None

    metrics = ["avg_amount", "min_amount", "max_amount", "count"]
    # Angles for radar chart
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False)
    angles = np.concatenate([angles, [angles[0]]])  # close the loop

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, polar=True)

    for cluster_id, profile in cluster_profiles.items():
        values = [float(profile.get(m, 0.0)) for m in metrics]
        values = np.concatenate([values, [values[0]]])
        ax.plot(angles, values, label=f"Cluster {cluster_id}", linewidth=2)
        ax.fill(angles, values, alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(
        ["Avg", "Min", "Max", "#Txns"],
        fontsize=11,
    )
    ax.set_title("Cluster Profiles (Radar View)", fontsize=15, pad=20)
    ax.grid(True)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))

    fig.tight_layout()
    output_path = Path(output_dir) / "cluster_radar.png"
    fig.savefig(output_path)
    plt.close(fig)
    logger.info("Saved radar chart to: %s", output_path)
    return str(output_path)


def generate_cashflow_waterfall(
    df: pd.DataFrame,
    output_dir: Path,
) -> str | None:
    """
    Simple waterfall-style view of net cash flow over months.
    Uses monthly net (sum of 'amount') as steps.
    """
    if "date" not in df.columns or "amount" not in df.columns:
        logger.info("Skipping waterfall: 'date' or 'amount' column missing.")
        return None

    if df.empty:
        logger.info("Skipping waterfall: empty dataframe.")
        return None

    df_local = df.copy()
    df_local["month"] = df_local["date"].dt.to_period("M").dt.to_timestamp()
    monthly_net = df_local.groupby("month")["amount"].sum().sort_index()

    if monthly_net.empty:
        logger.info("Skipping waterfall: no monthly data.")
        return None

    months = monthly_net.index
    values = monthly_net.values

    # Build cumulative waterfall steps
    cumulative = np.cumsum(values)
    fig, ax = plt.subplots(figsize=(9, 5))

    colors = ["#22c55e" if v >= 0 else "#ef4444" for v in values]
    ax.bar(months, values, color=colors)
    ax.plot(months, cumulative, marker="o", linestyle="--", linewidth=1.5)

    ax.set_title("Monthly Net Cash Flow (Waterfall-style)", fontsize=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Net Amount")
    ax.axhline(0, color="gray", linewidth=1)
    fig.autofmt_xdate()
    fig.tight_layout()

    output_path = Path(output_dir) / "cashflow_waterfall.png"
    fig.savefig(output_path)
    plt.close(fig)
    logger.info("Saved waterfall chart to: %s", output_path)
    return str(output_path)


def generate_cashflow_forecast(
    df: pd.DataFrame,
    output_dir: Path,
) -> str | None:
    """
    Very lightweight 'forecast': groups by month, then projects
    one extra month as the mean of the last three months.
    """
    if "date" not in df.columns or "amount" not in df.columns:
        logger.info("Skipping forecast: 'date' or 'amount' column missing.")
        return None

    if df.empty:
        logger.info("Skipping forecast: empty dataframe.")
        return None

    df_local = df.copy()
    df_local["month"] = df_local["date"].dt.to_period("M").dt.to_timestamp()
    monthly_net = df_local.groupby("month")["amount"].sum().sort_index()

    if monthly_net.empty:
        logger.info("Skipping forecast: no monthly data.")
        return None

    months = list(monthly_net.index)
    values = list(monthly_net.values)

    # Naive forecast = mean of last up-to-3 months
    tail = values[-3:]
    forecast_value = float(np.mean(tail))
    last_month = months[-1]
    # next month = last_month + 1 month
    next_month = (last_month.to_period("M") + 1).to_timestamp()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(months, values, marker="o", label="Actual")

    ax.plot(
        [next_month],
        [forecast_value],
        marker="o",
        linestyle="none",
        label="Forecast",
    )
    ax.plot(
        [months[-1], next_month],
        [values[-1], forecast_value],
        linestyle="--",
    )

    ax.set_title("Monthly Net Cash Flow + Simple Forecast", fontsize=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Net Amount")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()

    output_path = Path(output_dir) / "cashflow_forecast.png"
    fig.savefig(output_path)
    plt.close(fig)
    logger.info("Saved forecast chart to: %s", output_path)
    return str(output_path)


def generate_advanced_plots(
    df: pd.DataFrame,
    output_dir: str | Path,
    cluster_profiles: dict[int, dict[str, float]] | None = None,
) -> dict[str, str]:
    """
    Wrapper to generate extra plots without touching the original tests
    that exercise generate_all_plots().
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    figures: dict[str, str] = {}

    heatmap_path = generate_correlation_heatmap(df, output_path)
    if heatmap_path:
        figures["correlation_heatmap"] = heatmap_path

    radar_path = generate_cluster_radar_chart(cluster_profiles, output_path)
    if radar_path:
        figures["cluster_radar"] = radar_path

    waterfall_path = generate_cashflow_waterfall(df, output_path)
    if waterfall_path:
        figures["cashflow_waterfall"] = waterfall_path

    forecast_path = generate_cashflow_forecast(df, output_path)
    if forecast_path:
        figures["cashflow_forecast"] = forecast_path

    logger.info("Generated %s advanced visualization(s)", len(figures))
    return figures
