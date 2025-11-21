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



---
### Installation
Prerequisites

Python 3.10+ (project currently tested on Python 3.13)

pip

Git

Setup

Clone the repository:

git clone https://github.com/Hardhik-Poosa/TechSophy-Hardhik.git
cd TechSophy-Hardhik


Create and activate a virtual environment (recommended):

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate


Install dependencies:

pip install --upgrade pip
pip install -r requirements.txt

Usage

The main entrypoint is main.py, which runs the full pipeline.

Basic usage:

python main.py --input data/input_transactions.csv


Optional arguments:

python main.py --input path/to/transactions.csv --output outputs_dir --verbose


--input (required): Path to CSV file with transactions

--output (optional): Directory for generated reports and charts (default: outputs)

--verbose (optional): Enables more detailed logging

Expected input CSV columns:

Transaction Date (e.g., 2025-01-15, 15/02/2025, Mar 10, 2025)

Description

Amount

Transaction_Type (Debit or Credit)

Quality and Testing
Running Tests with Coverage

Locally you can use the provided PowerShell script:

.\quality.ps1


Or directly via pytest:

pytest tests --cov=src --cov-report=term-missing


HTML coverage report:

pytest tests --cov=src --cov-report=html
# Open htmlcov/index.html in a browser

Linting (Ruff / Flake8)

Run ruff:

ruff check .


If you also use flake8:

flake8 src tests

Security Scan (Bandit)
bandit -c bandit.yaml -r src

Pre-commit Hooks

Pre-commit hooks ensure linting and basic checks run before every commit.

Install hooks:

pre-commit install


Run hooks manually on all files:

pre-commit run --all-files


This keeps the repository consistent and prevents low-quality code from being committed.

CI/CD

GitHub Actions are configured in .github/workflows/ci.yml to run on every push and pull request:

ruff linting

Pytest with coverage

Bandit security scan

Pull requests into protected branches must pass this pipeline before merging.

Design and Architecture

Key principles:

Separation of concerns
Each module has a single responsibility (ingestion, preprocessing, ML, analysis, recommendations, visualization, orchestration).

Config-driven behavior
Tunable parameters (cluster count, contamination rate, thresholds) live in config.yaml, not hardcoded in code.

Typed, documented interfaces
Functions and classes use type hints and docstrings for readability and tooling support.

Defensive programming

Input validation in ingestion.py

Domain-specific exceptions: DataValidationError, ModelError

Well-defined error handling in runner.py

Observability

Structured logging across modules

Clear pipeline step logging in runner.run_pipeline

How to Contribute

Create a feature branch from development:

git checkout development
git pull
git checkout -b feature/your-feature-name


Make changes and run local checks:

.\quality.ps1
pre-commit run --all-files


Commit and push your branch:

git add .
git commit -m "Describe your change"
git push origin feature/your-feature-name


Open a Pull Request into development, and once reviewed, merge from development into main as per project workflow.

License

This repository is currently intended for educational and evaluation purposes.
If required, a formal license can be added later (for example, MIT or Apache-2.0).
