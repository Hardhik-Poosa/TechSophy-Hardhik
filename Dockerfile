# Dockerfile  (backend)

FROM python:3.11-slim

# Prevent Python from writing .pyc & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for pandas, numpy, sklearn, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# ⚠️ If your FastAPI app is not in main.py:app, change this line.
# For example, if it's src/api.py with "app", use: "src.api:app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
