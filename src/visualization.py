# src/visualization.py

"""
Visualization module.

Generates charts and graphs for spending analysis.
Saves publication-quality figures to disk.

Design Decisions:
    - Matplotlib/Seaborn for professional-quality visualizations
    - Consistent styling across all charts
    - Save to files rather than display (suitable for CLI/batch processing)
    - Configurable output format and DPI
"""

from pathlib import Path
from typing import Dict, Optional
import warnings

import pandas as pd
import matplotlib

# Use a non-interactive backend suitable for CLI and tests
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


from src.logging_config import get_logger
from src.config import get_visualization_config

# Suppress matplotlib warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

logger = get_logger(__name__)


def _setup_plot_style() -> None:
    """
    Configure matplotlib/seaborn style for consistent, professional plots.

    Design Decision:
        Centralized styling ensures visual consistency.
        Seaborn theme provides modern, clean aesthetics.
    """
    config = get_visualization_config()
    style = config.get("style", "seaborn-v0_8-darkgrid")

    try:
        plt.style.use(style)
    except Exception:
        # Fallback to default if style not available
        sns.set_theme()

    # Set color palette
    sns.set_palette("husl")


def _save_figure(fig: plt.Figure, output_path: str) -> str:
    """
    Save figure to disk with configured parameters.

    Args:
        fig: Matplotlib figure object
        output_path: Path to save the figure

    Returns:
        Absolute path to saved figure

    Design Decision:
        Centralized save logic ensures consistency.
        Creates output directory if needed.
    """
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


def plot_category_spend(
    category_stats: pd.DataFrame,
    output_dir: str,
) -> Optional[str]:
    """
    Create bar chart of spending by category.

    Args:
        category_stats: Category aggregation DataFrame
        output_dir: Directory to save the chart

    Returns:
        Path to saved figure, or None if no data
    """
    logger.info("Generating category spending chart")

    if category_stats.empty:
        logger.warning("No category data to plot")
        return None

    _setup_plot_style()
    config = get_visualization_config()
    figsize = tuple(config.get("figure_size", [10, 6]))

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

    output_path = Path(output_dir) / "category_spending.png"
    return _save_figure(fig, str(output_path))


def plot_spend_over_time(
    time_series: pd.DataFrame,
    output_dir: str,
) -> Optional[str]:
    """
    Create line chart of spending trends over time.

    Args:
        time_series: Monthly aggregation DataFrame
        output_dir: Directory to save the chart

    Returns:
        Path to saved figure, or None if no data
    """
    logger.info("Generating time series chart")

    if time_series.empty:
        logger.warning("No time series data to plot")
        return None

    _setup_plot_style()
    config = get_visualization_config()
    figsize = tuple(config.get("figure_size", [10, 6]))

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

    output_path = Path(output_dir) / "spending_trends.png"
    return _save_figure(fig, str(output_path))


def plot_anomalies(
    df: pd.DataFrame,
    output_dir: str,
) -> Optional[str]:
    """
    Create scatter plot highlighting anomalous transactions.

    Args:
        df: Transaction DataFrame with 'is_anomaly' column
        output_dir: Directory to save the chart

    Returns:
        Path to saved figure, or None if no data
    """
    logger.info("Generating anomaly visualization")

    if "is_anomaly" not in df.columns:
        logger.warning("No anomaly data to plot")
        return None

    _setup_plot_style()
    config = get_visualization_config()
    figsize = tuple(config.get("figure_size", [12, 6]))

    fig, ax = plt.subplots(figsize=figsize)

    normal = df.loc[df["is_anomaly"] == False]
    ax.scatter(
        normal["date"],
        normal["amount"],
        alpha=0.5,
        s=50,
        c="blue",
        label="Normal",
    )

    anomalies = df.loc[df["is_anomaly"] == True]
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

    output_path = Path(output_dir) / "anomaly_detection.png"
    return _save_figure(fig, str(output_path))


def plot_cluster_distribution(
    df: pd.DataFrame,
    output_dir: str,
) -> Optional[str]:
    """
    Create visualization of spending clusters.

    Args:
        df: Transaction DataFrame with 'cluster_id' column
        output_dir: Directory to save the chart

    Returns:
        Path to saved figure, or None if no data
    """
    logger.info("Generating cluster distribution chart")

    if "cluster_id" not in df.columns:
        logger.warning("No cluster data to plot")
        return None

    _setup_plot_style()
    config = get_visualization_config()
    figsize = tuple(config.get("figure_size", [10, 6]))

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

    output_path = Path(output_dir) / "cluster_distribution.png"
    return _save_figure(fig, str(output_path))


def generate_all_plots(
    analysis_result: Dict,
    df: pd.DataFrame,
    output_dir: str,
) -> Dict[str, str]:
    """
    Generate all visualization charts.

    Args:
        analysis_result: Analysis output dictionary
        df: Transaction DataFrame with predictions
        output_dir: Directory to save all charts

    Returns:
        Dictionary mapping chart names to file paths
    """
    logger.info(f"Generating all plots in directory: {output_dir}")

    figure_paths: Dict[str, str] = {}

    category_stats = analysis_result.get("category_stats", pd.DataFrame())
    path = plot_category_spend(category_stats, output_dir)
    if path:
        figure_paths["category_spending"] = path

    time_series = analysis_result.get("time_series", pd.DataFrame())
    path = plot_spend_over_time(time_series, output_dir)
    if path:
        figure_paths["spending_trends"] = path

    path = plot_anomalies(df, output_dir)
    if path:
        figure_paths["anomaly_detection"] = path

    path = plot_cluster_distribution(df, output_dir)
    if path:
        figure_paths["cluster_distribution"] = path

    logger.info(f"Generated {len(figure_paths)} visualization(s)")
    return figure_paths
