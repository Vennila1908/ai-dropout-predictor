[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\.."
$venv = Join-Path $repo "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venv)) {
  Write-Host "Backend venv missing. Run .\scripts\setup.ps1 first." -ForegroundColor Red
  exit 1
}
Push-Location (Join-Path $repo "backend")
try {
  & $venv -m app.db.seed_risk_demos
} finally {
  Pop-Location
}
