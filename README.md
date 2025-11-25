````markdown
# TechSophy – Smart Personal Finance Insights

TechSophy is a **full-stack personal finance analytics platform** that combines:

* **FastAPI** (Python backend)
* **React** (frontend dashboard)
* **Machine Learning** (clustering & anomaly detection)
* **BERT** (transaction category prediction)
* **LLM (Gemini API)** for AI-generated monthly spending summaries
* **Docker + CI/CD** with strong linting, testing & security

You upload a transaction CSV, and the system:

1.  Cleans & normalizes your transactions
2.  Predicts spending categories using a fine-tuned **BERT** model
3.  Clusters your spending habits
4.  Detects anomalies
5.  Generates plots & insights
6.  **(NEW)** Calls **Google Gemini 2.5 Flash** to generate a *human-like monthly financial summary*
7.  Produces a downloadable recommendations file

---

# 🚀 New Feature: LLM-Powered Monthly Summaries

The platform now includes an **LLM Insights Engine** under:
`POST /api/llm/summary`

### What it does

* Reads the processed transactions from the latest pipeline run
* Builds a compact JSON payload containing:
    * total spending
    * per-category spending breakdown
    * highest-spend merchants
    * top anomalies
    * cluster summaries
* Sends this to **Gemini 2.5 Flash**
* Returns a **natural language monthly summary** for the user

### Example:

> “In January 2025, your total spending was ₹42,310.
> Food & Dining accounted for the largest share.
> Your biggest merchant was Swiggy, followed by Amazon...”

### Requirements

Add your Gemini API key to `.env`:
`GEMINI_API_KEY=your_key_here`

Backend loads this in: `src/llm_service.py` and `src/llm_routes.py`. If the key is invalid or rate-limited, the API returns a clean 500 with a clear error message.

---

# 📐 Architecture / Project Structure

```text
.
├─ Dockerfile                      # Backend container
├─ docker-compose.yml              # Runs API + frontend + nginx
├─ .env.example                    # Add your Gemini API key here
├─ .github/workflows/ci.yml        # Full CI (lint, tests, bandit, coverage)
│
├─ frontend/
│  ├─ src/Dashboard.jsx           # UI shows LLM summary + graphs
│  └─ Dockerfile
│
├─ src/
│  ├─ api.py                      # FastAPI routes
│  ├─ llm_routes.py               # NEW: LLM API endpoints
│  ├─ llm_service.py              # NEW: Calls Gemini + prompt builder
│  ├─ preprocessing.py            # Feature engineering
│  ├─ category_model.py           # BERT model inference
│  ├─ ml_engine.py                # clustering + anomaly detection
│  ├─ visualization.py            # Matplotlib & seaborn charts
│  ├─ runner.py                   # Full pipeline orchestration
│  └─ logging_config.py
│
├─ scripts/
│  ├─ train_bert_categories.py    # Fine-tune BERT locally
│  └─ generate_category_dataset.py
│
├─ outputs/                        # Generated files (gitignored)
└─ models/
   ├─ bert_category_model/         # Local BERT weights
   └─ category_model_metrics.json
````

-----

# ⚙️ Setup (Local)

## 1\. Installation

### Backend (Python)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate

pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## 📥 CSV Format Requirements (VERY IMPORTANT)

Your CSV must have these columns:

| Column        | Type              | Required | Notes                      |
| ------------- | ----------------- | -------- | -------------------------- |
| `date`        | YYYY-MM-DD        | ✔        | Required for time features |
| `time`        | HH:MM or HH:MM:SS | Optional | Better anomaly detection   |
| `description` | Text              | ✔        | Used by BERT model         |
| `amount`      | Number            | ✔        | Must be numeric            |
| `merchant`    | Text              | Optional | Used for insights          |



**Do NOT use:**

  * `“₹500”` → must be `500` (numeric only)
  * `“12/31/24”` → must be `2024-12-31`
  * Extra spaces in column names

**Valid CSV example:**

```csv
date,time,description,amount,merchant
2025-01-03,14:30,Zomato Order,450,Zomato
2025-01-04,19:10,Uber Ride,320,Uber
2025-01-05,12:00,Amazon Purchase,1299,Amazon
2025-01-06,09:50,Cafe Coffee Day,180,CCD
```

## 🤖 ML Pipeline

The data pipeline runs sequentially:

1.  **Preprocessing:** Column normalization, feature extraction, base categorization.
2.  **BERT Classification:** Predicts final transaction categories.
3.  **Clustering (KMeans):** Groups similar spending behaviors.
4.  **Anomaly Detection (IsolationForest):** Detects unusual spending patterns.
5.  **Recommendations:** Generates actionable advice.
6.  **LLM Monthly Summary:** Uses Gemini to synthesize insights and financial tips.

-----

## 🧪 Testing & Quality

### Run tests:

```bash
pytest tests --cov=src --cov-report=term-missing
```

### Linting & security:

```bash
ruff check .
flake8 .
bandit -c bandit.yaml -r src
```

### Pre-commit:

```bash
pre-commit run --all-files
```

The **CI pipeline** (`.github/workflows/ci.yml`) runs all these checks: `Ruff`, `Pre-commit`, `Pytest`, `Coverage`, and `Bandit`, ensuring code quality is enforced on every commit.

-----

## 🐳 Docker (Full Stack)

Run the entire stack (FastAPI backend + React/Nginx frontend) with one command.

```bash
docker compose build
docker compose up -d
```

| Service | Address | Notes |
| :--- | :--- | :--- |
| **Backend (API)** | `http://localhost:8000` | FastAPI and LLM endpoints |
| **Frontend (UI)** | `http://localhost:3000` | React dashboard |

## 📦 Outputs

Each API run generates a unique directory under `outputs/api-runs/<run_id>/` containing all analytical artifacts:

  * `input.csv`
  * `processed_transactions.csv`
  * `cashflow_forecast.png`, `category_plot.png`, etc.
  * `recommendations.txt`
  * `llm_summary.txt` **(NEW)**

-----

## 🧠 Future Enhancements

  * Improve LLM prompts for even richer financial insights.
  * Support multiple models (OpenAI / Gemini / Llama selectable).
  * Fine-tune BERT with additional merchant datasets.
  * Add monthly budgeting predictions and user accounts + authentication.
  * Cloud deployment on Render / GCP / AWS.

-----

**🙌 Author**
Hardhik Poosa (Woxsen University)

Backend • ML • Frontend • DevOps

Project repo: TechSophy – Smart Personal Finance Insights

```
```
