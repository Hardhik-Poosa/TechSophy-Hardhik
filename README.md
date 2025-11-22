Below is your **clean, professional, fully rewritten README.md**,
**without emojis**, **production-grade style**, **includes all new updates**:

* New frontend (React, dark UI)
* New backend advanced charts (heatmap, radar, waterfall, forecast)
* Dashboard integration
* API redesigned with /analyze supporting additional figures
* Outputs now ignored from Git
* Maintains clean architecture and engineering depth

You can **copy this directly** into `README.md`.

---

```markdown
# TechSophy Finance Insights
A production-ready financial analytics platform combining Machine Learning, statistical modeling, a modern React dashboard, and a secure FastAPI backend.

This project demonstrates clean architecture, strong engineering practices, and a fully integrated end-to-end ML workflow for personal financial intelligence.

---

# Overview

TechSophy Finance Insights processes raw banking transactions, performs automated feature engineering, identifies patterns and anomalies using ML models, and renders insights through a modern, dark-themed analytics dashboard.

The system includes:

- Data ingestion and validation
- Feature engineering and preprocessing
- ML clustering (KMeans) and anomaly detection (Isolation Forest)
- Time-series and statistical analysis
- Multiple financial visualizations
- A React dashboard that displays insights, charts, and recommendations
- Clean, secure, typed Python backend using FastAPI

---

# Key Features

## Financial Analysis
- Total spend, income, net cash flow, and processed volume
- Month-over-month spending trends
- Category-level spending distribution
- Detection of recurring charges and subscription patterns
- Detection of risky, unusual, or irregular transactions

## Machine Learning
- KMeans clustering for behavioral segmentation
- Isolation Forest for anomaly detection
- Text vectorization for transaction descriptions (TF-IDF)
- Numerical, temporal, and categorical feature engineering
- Robust scaling and feature matrix construction

## Visualizations (Backend-Generated PNG Charts)
Standard charts:
- category_spending.png
- spending_trends.png
- anomaly_detection.png
- cluster_distribution.png

Advanced charts:
- correlation_heatmap.png
- cluster_radar.png
- cashflow_waterfall.png
- cashflow_forecast.png

All charts are served from `/static/...` and consumed by the React UI.

## Engineering Practices
- Fully modular clean architecture
- Strong type-hints and documentation
- Separate domains for ingestion, ML, analysis, visualization, reporting
- Strict linting: Ruff + Flake8
- Security analysis using Bandit
- Automated formatting and quality enforcement via pre-commit
- CI pipeline for tests, linting, coverage, and security
- Output data excluded from version control

---

# Project Structure

```

TechSophy-Hardhik/
├── src/
│   ├── analysis.py                 # Metric computation and analysis logic
│   ├── api.py                      # FastAPI server and /analyze endpoint
│   ├── config.py                   # Config loading and defaults
│   ├── ingestion.py                # CSV ingestion, validation, cleaning
│   ├── logging_config.py           # Structured logging setup
│   ├── ml_engine.py                # Clustering + anomaly models
│   ├── models.py                   # Dataclasses, schemas, errors
│   ├── preprocessing.py            # Feature engineering + scaling
│   ├── recommendations.py          # Insight generation
│   ├── visualization.py            # All charts (basic + advanced)
│   └── runner.py                   # Full pipeline orchestration
│
├── frontend/
│   ├── src/
│   │   ├── App.js                 # Main UI / upload + dashboard
│   │   ├── App.css                # Dark UI styling
│   │   └── Dashboard.jsx          # Extended dashboard page
│   └── public/
│
├── tests/                          # Unit + integration tests
│
├── data/
│   └── input_transactions.csv
│
├── outputs/                        # Generated files (ignored from git)
│   └── api-runs/<uuid>/*.png
│
├── .github/workflows/ci.yml        # CI pipeline
├── .pre-commit-config.yaml         # Hooks for quality enforcement
├── ruff.toml                       # Ruff config
├── pytest.ini                      # Pytest configuration
├── config.yaml                     # Application parameters
├── requirements.txt                # Dependencies
├── quality.ps1                     # Local quality check script
└── README.md

````

---

# Installation

## Requirements
- Python 3.10+
- Node.js 18+ (for React dashboard)
- pip
- Git

Clone the repository:

```bash
git clone https://github.com/Hardhik-Poosa/TechSophy-Hardhik.git
cd TechSophy-Hardhik
````

Create environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

---

# Running the Application

## Start Backend (FastAPI)

```bash
uvicorn src.api:app --reload --port 8000
```

Backend runs at:

```
http://127.0.0.1:8000
```

Static charts served at:

```
http://127.0.0.1:8000/static/<run-id>/<filename>.png
```

## Start Frontend (React)

```bash
cd frontend
npm start
```

Frontend UI runs at:

```
http://localhost:3000
```

---

# Using the /analyze Endpoint

Upload a CSV file containing:

| Column           | Example        |
| ---------------- | -------------- |
| Transaction Date | 2025-01-15     |
| Description      | UBER TRIP      |
| Amount           | 45.20          |
| Transaction_Type | Debit / Credit |

Returns:

* Summary metrics
* Recommendations
* Figure URLs (PNG)
* Run ID
* Processed CSV

---

# Testing & Quality

Run full quality suite:

```bash
.\quality.ps1
```

Run tests with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

Open HTML coverage:

```bash
pytest --cov=src --cov-report=html
```

Run linters:

```bash
ruff check .
flake8 .
```

Run security scan:

```bash
bandit -c bandit.yaml -r src
```

Run pre-commit:

```bash
pre-commit run --all-files
```

---

# Architecture Notes

## Clean Layered Pipeline

```
ingestion
→ preprocessing
→ ml_engine
→ analysis
→ recommendations
→ visualization (charts)
→ runner (orchestration)
→ FastAPI endpoint
→ React dashboard
```

## Principles

* Separation of concerns
* Config-driven parameters
* Fully typed domain models
* Defensive validation and error handling
* Logging across all pipeline stages
* Testability and reproducibility
* Git-ignored outputs to prevent repo pollution

---

# Contributing

```bash
git checkout development
git pull
git checkout -b feature/my-feature
```

Before committing:

```bash
pre-commit run --all-files
.\quality.ps1
```

Push changes and open a PR into `development`.

---

# License

Project is intended for educational and engineering demonstration purposes.
A formal open-source license may be added later.

---

# End of Documentation
