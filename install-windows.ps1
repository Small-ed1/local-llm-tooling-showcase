$ErrorActionPreference = "Stop"

$ProjectPath = "$HOME\local-llm-tooling-showcase"

Write-Host ""
Write-Host "== local-llm-tooling-showcase Windows installer ==" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path $ProjectPath)) {
    Write-Host "Project folder not found:" -ForegroundColor Red
    Write-Host $ProjectPath
    Write-Host ""
    Write-Host "Put the repo folder there first, then rerun this script."
    exit 1
}

cd $ProjectPath

if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    py -3.11 -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "Installing Windows curses compatibility..." -ForegroundColor Yellow
python -m pip install windows-curses

Write-Host "Installing test tools..." -ForegroundColor Yellow
python -m pip install pytest

Write-Host "Installing project..." -ForegroundColor Yellow
python -m pip install -e .

Write-Host ""
Write-Host "Install complete." -ForegroundColor Green
Write-Host ""
Write-Host "Starting server..."
Write-Host ""

tooling-showcase serve
