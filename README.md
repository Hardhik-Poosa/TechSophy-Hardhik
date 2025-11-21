# TechSophy Finance Insights

TechSophy Finance Insights is a production-ready Python application that analyzes personal spending patterns using machine learning and generates clear, actionable financial insights.

The project demonstrates:

- Clean, modular architecture
- Practical machine learning (clustering and anomaly detection)
- Strong testing and quality gates
- Security-conscious coding practices

---

## Features

### Analysis and Insights

- Income vs spending summary
- Category-wise spending breakdown
- Month-over-month trend analysis
- Detection of spending spikes by category
- Identification of recurring transactions (subscriptions, bills)

### Machine Learning

- **Clustering (KMeans)** to discover spending patterns
- **Anomaly Detection (Isolation Forest)** to flag unusual transactions
- Feature engineering for temporal, text-based, and numeric signals

### Engineering and Quality

- Layered, modular code structure (`ingestion → preprocessing → ML → analysis → recommendations → visualization`)
- Config-driven behavior via `config.yaml`
- Structured logging across all modules
- Extensive unit and integration tests with coverage reporting
- Static analysis and security scanning:
  - `ruff` / `flake8` for style and linting
  - `bandit` for security
- GitHub Actions CI pipeline (tests, coverage, linting, security)

---

## Project Structure

```text
TechSophy-Hardhik/
├── src/
│   ├── __init__.py
│   ├── analysis.py            # Business metrics and insight computation
│   ├── config.py              # Centralized configuration loading
│   ├── ingestion.py           # CSV loading, cleaning, schema validation
│   ├── logging_config.py      # Logging setup
│   ├── ml_engine.py           # Clustering and anomaly detection
│   ├── models.py              # Dataclasses and domain exceptions
│   ├── preprocessing.py       # Feature engineering and scaling
│   ├── recommendations.py     # Human-readable recommendations
│   ├── visualization.py       # Matplotlib/Seaborn visualizations
│   └── runner.py              # Full pipeline orchestration
│
├── tests/
│   ├── test_analysis_and_recommendations.py
│   ├── test_ingestion.py
│   ├── test_ml_engine.py
│   ├── test_ml_engine_exceptions.py
│   ├── test_preprocessing.py
│   ├── test_runner_integration.py
│   ├── test_visualization.py
│   └── conftest.py            # Shared test configuration (e.g., matplotlib backend)
│
├── data/
│   ├── input_transactions.csv                 # Sample raw data
│   └── input_transactions_with_labels.csv     # Optional labelled data
│
├── outputs/                                   # Generated reports (ignored in CI)
│   ├── summary.txt
│   ├── recommendations.txt
│   ├── processed_transactions.csv
│   ├── category_spending.png
│   ├── spending_trends.png
│   ├── anomaly_detection.png
│   └── cluster_distribution.png
│
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline (tests, coverage, lint, security)
│
├── .pre-commit-config.yaml     # Pre-commit hooks (ruff, black/format, etc.)
├── .flake8                     # Flake8 configuration (if used)
├── ruff.toml                   # Ruff configuration
├── bandit.yaml                 # Bandit configuration
├── pytest.ini                  # Pytest configuration
├── quality.ps1                 # Local quality script (tests + coverage + bandit)
├── config.yaml                 # Application configuration
├── requirements.txt            # Runtime and dev dependencies
├── main.py                     # CLI entrypoint
└── README.md                   # This file
