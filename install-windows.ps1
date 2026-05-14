$ErrorActionPreference = "Stop"

$ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$PythonCommand = Get-Command python -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "== local-llm-tooling-showcase Windows installer ==" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectPath

if ($PythonLauncher) {
    $PythonExe = "py"
    $VersionCommand = @("-3", "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)")
    $VenvCommand = @("-3", "-m", "venv", ".venv")
} elseif ($PythonCommand) {
    $PythonExe = "python"
    $VersionCommand = @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)")
    $VenvCommand = @("-m", "venv", ".venv")
} else {
    Write-Host "Python 3.11+ was not found. Install Python 3.11 and rerun this script." -ForegroundColor Red
    exit 1
}

& $PythonExe @VersionCommand
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python 3.11+ is required. Update your Python install and rerun this script." -ForegroundColor Red
    exit 1
}

if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $PythonExe @VenvCommand
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "Installing project with development tools..." -ForegroundColor Yellow
python -m pip install -e ".[dev]"

Write-Host "Running Python tests..." -ForegroundColor Yellow
python -m pytest tests/

Write-Host ""
Write-Host "Install complete." -ForegroundColor Green
Write-Host ""
Write-Host "Activate later with: .\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Green
Write-Host "Start the app with: tooling-showcase serve" -ForegroundColor Green
