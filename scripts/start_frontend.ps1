[CmdletBinding()]
param(
  [int]$Port = 5173,
  [string]$ApiBaseUrl = ""
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\.."
Push-Location (Join-Path $repo "frontend")
try {
  if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules missing - run npm install first (or .\scripts\setup.ps1)." -ForegroundColor Red
    exit 1
  }
  if ($ApiBaseUrl) {
    $env:VITE_API_BASE_URL = $ApiBaseUrl
  } elseif (-not $env:VITE_API_BASE_URL) {
    $env:VITE_API_BASE_URL = "http://localhost:8000"
  }
  # Pass port via env var; npm arg forwarding on Windows PowerShell is unreliable
  # (e.g. "npm run dev -- --port 5173" becomes "vite 5173" and breaks routing).
  $env:VITE_DEV_PORT = "$Port"
  npm run dev
} finally {
  Pop-Location
}
