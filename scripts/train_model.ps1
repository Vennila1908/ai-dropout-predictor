[CmdletBinding()]
param(
  [string]$Dataset = "",
  [string]$Output  = ""
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\.."
$venv = Join-Path $repo "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venv)) {
  Write-Host "Backend venv missing. Run .\scripts\setup.ps1 first." -ForegroundColor Red
  exit 1
}
if (-not $Dataset) { $Dataset = Join-Path $repo "datasets\sample_students.csv" }
if (-not $Output)  { $Output  = Join-Path $repo "ml\artifacts" }
& $venv (Join-Path $repo "ml\training_scripts\train_baseline.py") --dataset $Dataset --output $Output
