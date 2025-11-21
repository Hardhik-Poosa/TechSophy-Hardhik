FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command expects the CSV generated in data/
CMD ["python", "main.py", "--input", "data/input_transactions.csv"]
EXPOSE 8080