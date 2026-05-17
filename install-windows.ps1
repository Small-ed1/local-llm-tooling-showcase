param(
    [switch]$WithDesktop,
    [switch]$NoDesktop,
    [switch]$DesktopOnly,
    [switch]$RepairDesktop,
    [switch]$Yes
)

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

function Invoke-ShowcaseCli {
    param([string[]]$CliArgs)

    $PythonRunner = "python"
    $PythonPrefix = @()
    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        $PythonRunner = $PythonExe
        if ($PythonExe -eq "py") {
            $PythonPrefix = @("-3")
        }
    }

    & $PythonRunner @PythonPrefix -c "import tooling_showcase" 2>$null
    if ($LASTEXITCODE -eq 0) {
        & $PythonRunner @PythonPrefix -m tooling_showcase.cli @CliArgs
        return
    }

    $OldPythonPath = $env:PYTHONPATH
    if ($OldPythonPath) {
        $env:PYTHONPATH = "src;$OldPythonPath"
    } else {
        $env:PYTHONPATH = "src"
    }
    try {
        & $PythonRunner @PythonPrefix -m tooling_showcase.cli @CliArgs
    } finally {
        $env:PYTHONPATH = $OldPythonPath
    }
}

if ($DesktopOnly -or $RepairDesktop) {
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        .\.venv\Scripts\Activate.ps1
    }
    if ($RepairDesktop) {
        Invoke-ShowcaseCli @("desktop", "repair")
    } else {
        Invoke-ShowcaseCli @("desktop", "install")
    }
    exit $LASTEXITCODE
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

$NodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($NodeCommand) {
    Write-Host "Running frontend JavaScript syntax check..." -ForegroundColor Yellow
    node --check src/tooling_showcase/static/app-data.js
    node --check src/tooling_showcase/static/markdown.js
    node --check src/tooling_showcase/static/app.js
} else {
    Write-Host "Skipping JavaScript syntax check: node not found." -ForegroundColor Yellow
}

Write-Host "Running doctor..." -ForegroundColor Yellow
tooling-showcase doctor

Write-Host "Checking local Ollama model inventory..." -ForegroundColor Yellow
$BenchmarkSummary = python -m tooling_showcase.cli benchmark --shell-summary 2>$null
if ($LASTEXITCODE -eq 0) {
    $BenchmarkSummary | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "Ollama model inventory is unavailable. Start Ollama and run tooling-showcase benchmark later if you want model profiles." -ForegroundColor Yellow
}

if ($WithDesktop) {
    Write-Host "Installing optional desktop integration (user-level where supported; autostart disabled)." -ForegroundColor Yellow
    Invoke-ShowcaseCli @("desktop", "install")
} elseif ($NoDesktop) {
    Write-Host "Skipping optional desktop integration." -ForegroundColor Yellow
} elseif ($Yes) {
    Write-Host "Skipping optional desktop integration by default. Run tooling-showcase desktop install later to opt in." -ForegroundColor Yellow
} else {
    $DesktopReply = Read-Host "Install optional desktop integration? This may add a user-level launcher/service where supported, without autostart. [y/N]"
    if ($DesktopReply -match "^[Yy]$") {
        Invoke-ShowcaseCli @("desktop", "install")
    } else {
        Write-Host "Skipping optional desktop integration. Manage later with tooling-showcase desktop status/install/repair/uninstall." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Install complete." -ForegroundColor Green
Write-Host ""
Write-Host "Activate later with: .\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Green
Write-Host "Start the app with: tooling-showcase serve" -ForegroundColor Green
