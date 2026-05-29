<#
.SYNOPSIS
  One-shot bootstrap for the AI Dropout Predictor on Windows / PowerShell.

.DESCRIPTION
  - Creates a Python venv under backend/.venv and installs deps.
  - Installs frontend deps via npm.
  - Initializes the SQLite DB and seeds an admin + departments + sample students.
  - Trains an initial ML model from the sample dataset.
  - Prints next-step instructions.

.NOTES
  Run from the repo root:    .\scripts\setup.ps1
#>

[CmdletBinding()]
param(
  [switch]$SkipFrontend,
  [switch]$SkipTrain
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. "$PSScriptRoot\_lib.ps1"

$repoRoot   = Resolve-Path "$PSScriptRoot\.."
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$venvDir     = Join-Path $backendDir ".venv"

function Ensure-Tool([string]$name, [string]$hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Required tool '$name' not found on PATH. $hint"
  }
}

Write-Host "▶ Checking prerequisites..." -ForegroundColor Cyan

# Locate Python 3.11+ via the shared helper rather than blindly trusting
# whatever `python` happens to mean on this machine.
$pyInfo = Find-Python311Plus
if (-not $pyInfo.Found) {
  Write-Host "  ✗ No Python 3.11+ interpreter found. Tried:" -ForegroundColor Red
  foreach ($a in $pyInfo.Attempts) { Write-Host "      - $a" -ForegroundColor Red }
  Write-Host "  Install Python 3.11 or newer from https://www.python.org/downloads/" -ForegroundColor Red
  Write-Host "  Then close and re-open this terminal so PATH refreshes." -ForegroundColor Red
  throw "Python 3.11+ not found"
}
Write-Host ("  • Using Python {0} (via '{1}')" -f $pyInfo.Version, $pyInfo.Invoke) -ForegroundColor Yellow

if (-not $SkipFrontend) {
  Ensure-Tool node "Install Node.js 20+ from https://nodejs.org/"
  Ensure-Tool npm  "npm should ship with Node.js"
}

# ─── Backend venv + deps ───────────────────────────────────────────────────────
Write-Host "`n▶ Creating Python virtualenv at $venvDir" -ForegroundColor Cyan
if (-not (Test-Path $venvDir)) {
  & $pyInfo.Exe @($pyInfo.Args + '-m','venv',$venvDir)
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create virtualenv with '$($pyInfo.Invoke) -m venv'"
  }
}

$python = Join-Path $venvDir "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $backendDir "requirements.txt")

# ─── Backend env file ─────────────────────────────────────────────────────────
$envPath = Join-Path $backendDir ".env"
if (-not (Test-Path $envPath)) {
  Copy-Item (Join-Path $backendDir ".env.example") $envPath
  Write-Host "  • Created backend\.env from .env.example" -ForegroundColor Yellow
}

# ─── DB init + seed ───────────────────────────────────────────────────────────
Write-Host "`n▶ Initializing database + seeding admin/departments/sample students" -ForegroundColor Cyan
Push-Location $backendDir
try {
  & $python -m app.db.init_db
} finally {
  Pop-Location
}

# ─── Train initial model ──────────────────────────────────────────────────────
if (-not $SkipTrain) {
  Write-Host "`n▶ Training initial ML model" -ForegroundColor Cyan
  & $python (Join-Path $repoRoot "ml\training_scripts\train_baseline.py") `
      --dataset (Join-Path $repoRoot "datasets\sample_students.csv") `
      --output (Join-Path $repoRoot "ml\artifacts")
}

# ─── Frontend deps ────────────────────────────────────────────────────────────
if (-not $SkipFrontend) {
  Write-Host "`n▶ Installing frontend dependencies (this may take a minute)" -ForegroundColor Cyan
  Push-Location $frontendDir
  try {
    if (-not (Test-Path (Join-Path $frontendDir ".env.local"))) {
      Copy-Item (Join-Path $frontendDir ".env.example") (Join-Path $frontendDir ".env.local")
    }
    npm install --no-audit --no-fund --loglevel=error
  } finally {
    Pop-Location
  }
}

Write-Host "`n✔ Setup complete!" -ForegroundColor Green
Write-Host @"

Next steps:
  1. (Optional) Pull the local LLM model so AI recommendations work:
       .\scripts\pull_llm.ps1
  2. Start the backend (in one terminal):
       .\scripts\start_backend.ps1
  3. Start the frontend (in another terminal):
       .\scripts\start_frontend.ps1
  4. Open http://localhost:5173 and log in with:
       admin@example.com  /  Admin@123
"@ -ForegroundColor Cyan
