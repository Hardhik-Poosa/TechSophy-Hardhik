# src/visualization.py

"""
Visualization module.

Generates charts and graphs for spending analysis.
Saves publication-quality figures to disk.
"""

import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import get_visualization_config
from src.logging_config import get_logger

# ---- Safe backend configuration (flake8-compatible) ----
try:
    matplotlib.use("Agg", force=True)
except Exception:
    pass

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
