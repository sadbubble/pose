# Run POSE locally (frontend + API on http://127.0.0.1:8080)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$ApiDir = Join-Path $Root "pose\pose-api"
$DataDir = Join-Path $Root "pose\data"
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$env:DB_PATH = Join-Path $DataDir "pose.db"

Set-Location $ApiDir
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python is required. Install Python 3.11+ from https://www.python.org/downloads/"
}
python -m pip install -q -r requirements.txt
Write-Host ""
Write-Host "POSE is running at http://127.0.0.1:8080" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""
python -m uvicorn main:app --host 127.0.0.1 --port 8080 --reload
