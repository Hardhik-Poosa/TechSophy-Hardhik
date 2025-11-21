"""
Recommendation generation module.

Converts analysis results into human-readable recommendations.
"""

from __future__ import annotations

from typing import List

from src.config import get_business_rules_config
from src.logging_config import get_logger
from src.models import AnalysisResult

logger = get_logger(__name__)


class RecommendationEngine:
    """
    Converts numerical insights into textual recommendations.
    """

    def __init__(self) -> None:
        self.rules = get_business_rules_config()

    def generate_recommendations(self, analysis_result: AnalysisResult) -> List[str]:
        recs: List[str] = []
        recs.extend(self._recommend_on_cash_flow(analysis_result))
        recs.extend(self._recommend_on_category_spikes(analysis_result))
        recs.extend(self._recommend_on_anomalies(analysis_result))
        recs.extend(self._recommend_on_recurring(analysis_result))
        return recs

    # ------------------------------------------------------------------ #

    def _recommend_on_cash_flow(self, analysis_result: AnalysisResult) -> List[str]:
        s = analysis_result.summary
        if s.net_cash_flow < 0:
            return [
                (
                    "Your net cash flow over the analysed period is negative "
                    f"({s.net_cash_flow:.2f}). Consider reviewing high-spend categories "
                    "and setting monthly limits."
                )
            ]
        return []

    def _recommend_on_category_spikes(self, analysis_result: AnalysisResult) -> List[str]:
        threshold = float(self.rules.get("category_spike_threshold", 0.30))

        df = analysis_result.raw_df
        if "year_month" not in df.columns or "base_category" not in df.columns:
            return []

        grouped = (
            df.groupby(["year_month", "base_category"], as_index=False)
            .agg(total_amount=("amount", "sum"))
            .sort_values(["base_category", "year_month"])
        )

        recs: List[str] = []
        for category in grouped["base_category"].unique():
            series = grouped[grouped["base_category"] == category].reset_index(drop=True)
            if len(series) < 2:
                continue

            series["pct_change"] = series["total_amount"].pct_change()
            spikes = series[series["pct_change"] > threshold]
            for _, row in spikes.iterrows():
                recs.append(
                    (
                        f"Spending on category '{category}' increased by "
                        f"{row['pct_change'] * 100:.1f}% in {row['year_month']} "
                        f"(total {row['total_amount']:.2f}). Review recent purchases."
                    )
                )

        return recs

    def _recommend_on_anomalies(self, analysis_result: AnalysisResult) -> List[str]:
        anomalies = analysis_result.anomalies
        if anomalies.empty:
            return []

        descriptions = anomalies["description"].head(5).tolist()
        return [
            (
                f"{len(anomalies)} transactions were flagged as unusual. "
                f"Examples include: {', '.join(descriptions)}. "
                "Verify that these are legitimate."
            )
        ]

    def _recommend_on_recurring(self, analysis_result: AnalysisResult) -> List[str]:
        recurring = analysis_result.recurring
        if recurring.empty:
            return []

        top = recurring.sort_values("mean_amount", ascending=False).head(5)
        total_recurring = (top["mean_amount"] * top["num_occurrences"]).sum()

        names = top["sample_description"].tolist()
        return [
            (
                "Recurring transactions detected for: "
                f"{', '.join(names)}. Together they represent approximately "
                f"{total_recurring:.2f} over the analysed period. "
                "Consider cancelling any subscriptions you no longer need."
            )
        ]


_default_engine = RecommendationEngine()


def generate_recommendations(analysis_result: AnalysisResult) -> List[str]:
    return _default_engine.generate_recommendations(analysis_result)
