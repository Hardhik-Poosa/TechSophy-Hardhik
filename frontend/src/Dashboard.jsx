// frontend/src/Dashboard.jsx
import React, { useState } from "react";
import { Button, Spinner, Alert } from "react-bootstrap";
import "./App.css"; // reuse existing dark styles + dashboard rules

// Use the API_BASE URL from the environment or default to localhost:8000
const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

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
  const [modalSrc, setModalSrc] = useState(null);
  const [modalTitle, setModalTitle] = useState("");

  // --- AI SUMMARY STATE ---
  const [aiSummary, setAiSummary] = useState("");
  const [aiSummaryLoading, setAiSummaryLoading] = useState(false);
  const [aiSummaryError, setAiSummaryError] = useState("");
  // ------------------------

  const openModal = (src, title) => {
    setModalSrc(src);
    setModalTitle(title);
  };

  const closeModal = () => {
    setModalSrc(null);
    setModalTitle("");
  };

  // --- AI SUMMARY HANDLER ---
  async function handleAiSummaryClick() {
    if (!lastRunId) return;

    setAiSummaryLoading(true);
    setAiSummaryError("");
    setAiSummary("");

    try {
      const res = await fetch(`${API_BASE}/api/llm/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_id: lastRunId }),
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMessage =
          data.detail || "Failed to fetch AI summary from API.";
        throw new Error(errorMessage);
      }

      setAiSummary(data.summary || "");
    } catch (err) {
      console.error("AI Summary Error:", err);
      setAiSummaryError(err.message || "An unexpected error occurred.");
    } finally {
      setAiSummaryLoading(false);
    }
  }
  // ------------------------

  // Advanced visualizations
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
          {/* AI Summary Button */}
          <Button
            onClick={handleAiSummaryClick}
            disabled={!lastRunId || aiSummaryLoading || isAnalyzing}
            variant="success"
            className="btn-elevated"
          >
            {aiSummaryLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Generating…
              </>
            ) : (
              "🤖 Generate AI Summary"
            )}
          </Button>

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
        {/* AI Summary Display */}
        {(aiSummary || aiSummaryError) && (
          <section className="dashboard-section">
            <div className="dash-card card-glass dash-ai-card">
              <div className="dash-card-header">
                <h2 className="dash-card-title">🤖 AI Monthly Summary</h2>
              </div>
              <div className="dash-card-body">
                {aiSummaryError && (
                  <Alert variant="danger">
                    <strong>AI Generation Failed:</strong> {aiSummaryError}
                  </Alert>
                )}
                {aiSummary && (
                  <pre className="ai-summary-text">{aiSummary}</pre>
                )}
              </div>
            </div>
          </section>
        )}

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
                summary && summary.net_cash_flow >= 0 ? "Positive" : "Negative"
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

        {/* Middle row: ONLY recommendations now */}
        <section className="dashboard-section">
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

        {/* Advanced visual charts */}
        <section className="dashboard-section">
          <h2 className="dash-section-title">Advanced Analytics</h2>
          <div className="dash-grid dash-grid-4">
            <ChartCard
              title="Correlation Heatmap"
              subtitle="Relationships between numeric features."
              src={advHeatmap}
              onClick={() =>
                openModal(advHeatmap, "Feature Correlation Heatmap")
              }
            />
            <ChartCard
              title="Cluster Radar"
              subtitle="Profile of each cluster (avg / min / max / volume)."
              src={advRadar}
              onClick={() =>
                openModal(advRadar, "Cluster Profiles (Radar Chart)")
              }
            />
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
