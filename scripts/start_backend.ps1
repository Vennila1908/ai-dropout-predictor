[CmdletBinding()]
param(
  [int]$Port = 8000,
  [switch]$NoReload
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\.."
$venv = Join-Path $repo "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venv)) {
  Write-Host "Backend venv missing. Run .\scripts\setup.ps1 first." -ForegroundColor Red
  exit 1
}
Push-Location (Join-Path $repo "backend")
try {
  $args = @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$Port")
  if (-not $NoReload) { $args += "--reload" }
  & $venv @args
} finally {
  Pop-Location
}
