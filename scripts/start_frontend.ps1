[CmdletBinding()]
param([int]$Port = 5173)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\.."
Push-Location (Join-Path $repo "frontend")
try {
  if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules missing — run npm install first (or .\scripts\setup.ps1)." -ForegroundColor Red
    exit 1
  }
  $env:VITE_API_BASE_URL = $env:VITE_API_BASE_URL ?? "http://localhost:8000"
  npm run dev -- --port $Port --host
} finally {
  Pop-Location
}
