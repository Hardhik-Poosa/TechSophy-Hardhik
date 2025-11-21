# quality.ps1
# Run automated quality checks:
# - Unit tests with coverage
# - Coverage reports (terminal + HTML)
# - Bandit security scan

Write-Host "Running tests with coverage..."
pytest tests `
  --cov=src `
  --cov-report=term-missing `
  --cov-report=html

Write-Host ""
Write-Host "HTML coverage report generated in ./htmlcov/index.html"
Write-Host ""

Write-Host "Running Bandit security scan..."
bandit -c bandit.yaml -r src
