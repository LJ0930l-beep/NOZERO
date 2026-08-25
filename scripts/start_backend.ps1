param(
  [int]$Port = 8000
)

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
python scripts/seed_data.py
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port $Port
