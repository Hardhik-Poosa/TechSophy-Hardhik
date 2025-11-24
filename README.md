# TechSophy – Smart Personal Finance Insights

This project is a full-stack personal finance analytics tool built with:

- **FastAPI** (Python) for the backend API and ML pipeline
- **React** for the frontend dashboard
- **Scikit-learn + Transformers (BERT)** for:
  - Spending category classification
  - Spending pattern clustering
  - Anomaly detection on transactions

You upload your transaction CSV, and the app:

1. Cleans and enriches the data (time features, categories).
2. Clusters your spending patterns.
3. Detects unusual / anomalous transactions.
4. Generates visualizations and a human-readable `recommendations.txt`.

It’s fully Dockerized and has a CI pipeline with tests, linting and security checks.

---

## Tech Stack

**Backend**

- Python 3.11
- FastAPI / Uvicorn
- Pandas, NumPy
- scikit-learn (KMeans, IsolationForest)
- Hugging Face Transformers (BERT classifier)

**Frontend**

- React (JavaScript)
- Built and served via Nginx in production (Docker)

**DevOps / Quality**

- Docker + docker compose
- GitHub Actions CI
- `pytest` + coverage
- `ruff`, `flake8`, `bandit`
- `pre-commit` hooks (formatting, EOF, large-file checks)

---

## Project Structure (high-level)

```text
.
├─ Dockerfile                 # Backend image
├─ docker-compose.yml         # api + frontend services
├─ .dockerignore
├─ .gitignore
├─ .github/
│  └─ workflows/
│     └─ ci.yml              # CI pipeline
├─ frontend/
│  ├─ Dockerfile             # Frontend image
│  ├─ src/
│  │  ├─ App.js
│  │  └─ Dashboard.jsx
├─ scripts/
│  ├─ generate_category_dataset.py   # (optional) dataset generation
│  └─ train_bert_categories.py       # trains BERT classifier
├─ src/
│  ├─ api.py                  # FastAPI routes
│  ├─ category_model.py       # BERT category prediction (+ confidence)
│  ├─ ml_engine.py            # clustering + anomaly models
│  ├─ models.py               # model loading / orchestration
│  ├─ preprocessing.py        # feature engineering, categories
│  └─ logging_config.py
├─ data/
│  └─ training_categories.csv # labelled training data for categories
└─ models/
   ├─ bert_category_model/    # fine-tuned BERT weights (local only, gitignored)
   └─ category_model_metrics.json   # accuracy, macro F1, classes
````



## Setup – Local Development

### 1. Prerequisites

* Python **3.11**
* Node.js **16+** or **20+** (for the frontend)
* `pip`, `virtualenv` (recommended)
* Git

### 2. Clone the repo

```bash
git clone https://github.com/Hardhik-Poosa/TechSophy-Hardhik.git
cd TechSophy-Hardhik
```

### 3. Python environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# OR
.\.venv\Scripts\activate       # Windows PowerShell

python -m pip install --upgrade pip
pip install -r requirements.txt
```
### CSV Input Requirements

Your app expects a specific CSV format so the ML pipeline can correctly parse, clean, and analyze transactions.

# Required CSV Columns

Your CSV must contain the following headers exactly as shown:


| Column Name     | Type              | Description                                                         |
| --------------- | ----------------- | ------------------------------------------------------------------- |
| **date**        | YYYY-MM-DD        | Date of transaction *(required for time features, clustering)*      |
| **time**        | HH:MM or HH:MM:SS | Time of transaction *(optional but recommended)*                    |
| **description** | string            | Merchant or transaction description *(used by BERT category model)* |
| **amount**      | numeric           | Transaction amount *(positive for spending)*                        |

# Optional but Recommended

| Column Name  | Type   | Purpose                                                        |
| ------------ | ------ | -------------------------------------------------------------- |
| **merchant** | string | Used to generate merchant-level insights, anomaly explanations |
| **category** | string | If present, used for training datasets, not for pipeline input |


## IMPORTANT — READ THIS BEFORE USING THE APP

 Your CSV WILL NOT work unless the column names match exactly:
```bash
date, time, description, amount
```

date must be conver tible to pandas datetime
If it's in formats like 12/31/2024 or 31-12-2024, the system will attempt conversion but may fail.

description is required for the BERT model
– Used for category prediction
– Missing or empty descriptions reduce ML accuracy
– “Uncertain” category will appear if confidence is low

amount must be numeric
Strings like "₹500" or "500 INR" will break processing.

If time is missing, the app will still work —
but time-based features (hour-level analytics) won’t be generated.

## Example of a Valid CSV
date,time,description,amount,merchant
2025-01-03,14:30,Zomato Order,450,Zomato
2025-01-04,19:10,Uber Ride,320,Uber
2025-01-05,12:00,Amazon Purchase,1299,Amazon
2025-01-06,09:50,Cafe Coffee Day,180,CCD


# Add this to the README under a “CSV Format” section

Below is the section formatted cleanly for direct paste:

## CSV Format Requirements

Your transaction CSV must follow a strict format for the ML pipeline to work correctly.

# Required Columns

| Column        | Type                  | Description                        |
| ------------- | --------------------- | ---------------------------------- |
| `date`        | `YYYY-MM-DD`          | Date of the transaction            |
| `time`        | `HH:MM:SS` (or HH:MM) | Time of transaction (recommended)  |
| `description` | Text                  | Merchant / transaction description |
| `amount`      | Number                | Transaction amount                 |


# Optional Columns

| Column     | Purpose                                           |
| ---------- | ------------------------------------------------- |
| `merchant` | Improves cluster summaries & anomaly explanations |
| `category` | Only required when training your own dataset      |


## IMPORTANT

Do NOT rename columns.

Do NOT add extra spaces or special characters.

amount must be numeric (no ₹ symbol).

date must be parseable by pandas.

description is mandatory for BERT categorization.
---

## Training the BERT Category Model

This step trains the BERT-based classifier on `data/training_categories.csv` and saves:

* Fine-tuned model under: `models/bert_category_model/`
* Evaluation metrics under: `models/category_model_metrics.json`

Run:

```bash
python scripts/train_bert_categories.py
```

You should see something like:

* Train / val / test sizes logged.
* Test metrics printed (accuracy, macro F1, confusion matrix).
* A final message:

```text
Saved metrics to models/category_model_metrics.json
```

### How the category model is used

* `src/category_model.py` loads the **local** fine-tuned BERT model.

* It exposes:

  ```python
  predict_category(text: str) -> str
  ```

* If the confidence is below a threshold, it returns `"Uncertain"` so the UI can highlight it for manual review.

* If the model isn’t available or fails to load, code falls back to the rule-based categorization in `PreprocessingService`.

---

## Running the Backend (FastAPI)

From the repo root (with virtualenv activated):

```bash
uvicorn main:app --reload
# or (depending on your entrypoint)
uvicorn src.api:app --reload
```

Then open: [http://localhost:8000/docs](http://localhost:8000/docs) to see the FastAPI Swagger UI.

The API typically supports:

* Uploading a transactions CSV.
* Triggering the pipeline (preprocessing, clustering, anomaly detection).
* Returning processed data and generated file paths (plots, recommendations).

*(Adjust this description based on your actual routes in `src/api.py`.)*

---

## Running the Frontend (React)

```bash
cd frontend
npm install
npm start
```

This should start the React dev server on `http://localhost:3000`.

Make sure the frontend points its API calls to the backend (usually `http://localhost:8000`).
If needed, configure this via environment variables or a `config.js`.

---

## Docker – One Command Run

You can run the whole stack with Docker.

### 1. Build images

From repo root:

```bash
docker compose build
```

### 2. Run

```bash
docker compose up
# or detached
docker compose up -d
```

Services:

* **API**: [http://localhost:8000](http://localhost:8000)
* **Frontend**: [http://localhost:3000](http://localhost:3000)

`docker-compose.yml` defines two services:

* `api` – builds from `Dockerfile` in root (FastAPI backend).
* `frontend` – builds from `frontend/Dockerfile` (React + Nginx).

---

## Data & Outputs

The app writes outputs into the `outputs/` directory:

* Processed CSV: `outputs/processed_transactions.csv`
* Plots: cluster distributions, category spending, anomalies, etc.
* Human-readable insights: `outputs/recommendations.txt`

Per API run, outputs may also be organized under:

```text
outputs/api-runs/<run_id>/
```

containing:

* The specific input CSV for that run.
* Processed CSV.
* Plots/images.
* `summary.txt` and `recommendations.txt`.

These are **ignored by git** to keep the repo clean.

---

## Testing & Quality

### Run tests + coverage

```bash
pytest tests --cov=src --cov-report=term-missing
```

### Linting & security

```bash
ruff check .
flake8 .
bandit -c bandit.yaml -r src
```

### Pre-commit hooks

Before committing, run:

```bash
pre-commit run --all-files
```

Hooks include:

* Trailing whitespace and EOF fixes.
* Large file check (to avoid committing big model weights / logs).
* Ruff + formatting.
* Flake8.

The CI pipeline (`.github/workflows/ci.yml`) runs:

* `pre-commit` hooks
* `ruff` lint
* `pytest` with coverage
* `bandit` security scan
* Uploads `coverage.xml` as a build artifact

on every push / PR to `main` and `development`.

---

## Notes / Future Work

Some ideas to extend this project:

* Improve the BERT category model with more data and hyperparameter tuning.
* Expose category confidence and “Uncertain” flags clearly in the dashboard.
* Add more interpretable anomaly explanations on the UI.
* Persist user sessions / preferences in a database.
* Deploy to a cloud provider using the existing Docker setup.

---
