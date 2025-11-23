// frontend/src/Dashboard.jsx
import React from "react";
import "./App.css"; // reuse existing dark styles + new dashboard rules

function StatCard({ label, value, subtitle, accent }) {
  return (
    <div className="dash-card card-glass card-hover">
      <div className="dash-card-header">
        <span className="dash-card-label">{label}</span>
        {accent && <span className="dash-pill">{accent}</span>}
      </div>
      <div className="dash-card-value">{value}</div>
      {subtitle && <div className="dash-card-subtitle">{subtitle}</div>}
    </div>
  );
}

function ChartCard({ title, subtitle, src, onClick }) {
  if (!src) return null;

  return (
    <div className="dash-chart-card card-glass card-hover" onClick={onClick}>
      <div className="dash-chart-header">
        <div>
          <div className="dash-chart-title">{title}</div>
          {subtitle && <div className="dash-chart-subtitle">{subtitle}</div>}
        </div>
      </div>
      <div className="dash-chart-body">
        <img src={src} alt={title} className="chart-thumb" />
      </div>
    </div>
  );
}

export default function Dashboard({
  summary,
  recommendations,
  figures,
  isAnalyzing,
  lastRunId,
}) {
  const [modalSrc, setModalSrc] = React.useState(null);
  const [modalTitle, setModalTitle] = React.useState("");

  const openModal = (src, title) => {
    setModalSrc(src);
    setModalTitle(title);
  };

  const closeModal = () => {
    setModalSrc(null);
    setModalTitle("");
  };

  // Advanced visualizations (these are the only ones we keep)
  const advHeatmap = figures?.correlation_heatmap;
  const advRadar = figures?.cluster_radar;
  const advWaterfall = figures?.cashflow_waterfall;
  const advForecast = figures?.cashflow_forecast;

  return (
    <div className="app-root dashboard-root">
      <div className="app-overlay" />

      <header className="app-header dashboard-header">
        <div className="dash-header-left">
          <h1 className="app-title dashboard-title">
            Finance Insights{" "}
            <span className="dash-gradient-text">Dashboard</span>
          </h1>
          <p className="text-light-50 dash-header-subtitle">
            Upload a CSV and explore spending patterns, clusters, anomalies, and
            trends.
          </p>
        </div>
        <div className="dash-header-right">
          {lastRunId && (
            <span className="dash-badge">
              Run ID:
              <span className="dash-badge-id">{lastRunId.slice(0, 8)}</span>
            </span>
          )}
          {isAnalyzing && (
            <span className="dash-badge dash-badge-live">Analyzing…</span>
          )}
        </div>
      </header>

      <main className="dashboard-main">
        {/* Top row: key stats */}
        <section className="dashboard-section">
          <div className="dash-grid dash-grid-4">
            <StatCard
              label="Total Spend"
              value={
                summary ? `₹${summary.total_spend.toLocaleString()}` : "–"
              }
              subtitle="All outgoing transactions"
              accent="Expenses"
            />
            <StatCard
              label="Total Income"
              value={
                summary ? `₹${summary.total_income.toLocaleString()}` : "–"
              }
              subtitle="All incoming transactions"
              accent="Income"
            />
            <StatCard
              label="Net Cash Flow"
              value={
                summary ? `₹${summary.net_cash_flow.toLocaleString()}` : "–"
              }
              subtitle="Income minus spend"
              accent={
                summary && summary.net_cash_flow >= 0
                  ? "Positive"
                  : "Negative"
              }
            />
            <StatCard
              label="Transactions"
              value={summary ? summary.num_transactions : "–"}
              subtitle="Rows processed from CSV"
              accent="Volume"
            />
          </div>
        </section>

        {/* Middle row: anomalies (text only) + recommendations */}
        <section className="dashboard-section dash-section-2col">
          {/* Anomaly Snapshot WITHOUT image preview */}
          <div className="dash-card card-glass card-hover dash-anomaly-card">
            <div className="dash-card-header">
              <div>
                <h2 className="dash-card-title">Anomaly Snapshot</h2>
                <p className="dash-card-subtitle">
                  Outlier transactions spotted by the anomaly detector.
                </p>
              </div>
            </div>
            <div className="dash-empty-state">
              Anomaly insights are reflected in your statistics and
              recommendations.
            </div>
          </div>

          {/* Recommendations */}
          <div className="dash-card card-glass dash-rec-card">
            <div className="dash-card-header">
              <div>
                <h2 className="dash-card-title">Recommendations</h2>
                <p className="dash-card-subtitle">
                  Plain-language suggestions based on your spending patterns.
                </p>
              </div>
            </div>
            {recommendations && recommendations.length > 0 ? (
              <ul className="fancy-list dash-rec-list">
                {recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            ) : (
              <div className="dash-empty-state">
                Upload a CSV to generate tailored recommendations.
              </div>
            )}
          </div>
        </section>

        {/* Bottom: ONLY the advanced charts */}
        <section className="dashboard-section">
          <h2 className="dash-section-title">Visual Analytics</h2>
          <div className="dash-grid dash-grid-4">
            {/* Correlation Heatmap */}
            <ChartCard
              title="Correlation Heatmap"
              subtitle="Relationships between numeric features."
              src={advHeatmap}
              onClick={() =>
                openModal(advHeatmap, "Feature Correlation Heatmap")
              }
            />

            {/* Cluster Radar */}
            <ChartCard
              title="Cluster Radar"
              subtitle="Profile of each cluster (avg / min / max / volume)."
              src={advRadar}
              onClick={() =>
                openModal(advRadar, "Cluster Profiles (Radar Chart)")
              }
            />

            {/* Cashflow Waterfall */}
            <ChartCard
              title="Cashflow Waterfall"
              subtitle="Month-by-month net cash movement."
              src={advWaterfall}
              onClick={() =>
                openModal(
                  advWaterfall,
                  "Monthly Net Cash Flow (Waterfall-style)",
                )
              }
            />

            {/* Cashflow Forecast */}
            <ChartCard
              title="Cashflow Forecast"
              subtitle="Simple forecast from recent months."
              src={advForecast}
              onClick={() =>
                openModal(advForecast, "Net Cash Flow Forecast")
              }
            />
          </div>
        </section>
      </main>

      {/* Chart modal */}
      {modalSrc && (
        <div className="dash-modal-backdrop" onClick={closeModal}>
          <div
            className="dash-modal chart-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="dash-modal-header">
              <h3>{modalTitle}</h3>
              <button
                type="button"
                className="dash-modal-close"
                onClick={closeModal}
              >
                ✕
              </button>
            </div>
            <div className="dash-modal-body">
              <img src={modalSrc} alt={modalTitle} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
