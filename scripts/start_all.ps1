<#
.SYNOPSIS
  One-command end-to-end launcher for the AI Dropout Predictor (Windows / PowerShell).

.DESCRIPTION
  Performs prerequisite checks, runs setup if needed, ensures the local LLM
  (Ollama) is pulled & running when available, starts the FastAPI backend
  and the Vite frontend in their own terminal windows, waits for the
  backend /health endpoint, and opens the browser.

  Idempotent: safe to run multiple times. Reuses existing venv,
  node_modules, model artifact, and pulled Ollama models.

.NOTES
  Run from anywhere:    .\scripts\start_all.ps1
#>

[CmdletBinding()]
param(
  [int]$BackendPort  = 8000,
  [int]$FrontendPort = 5173,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\_lib.ps1"

# Paths (resolved relative to this script).
$repoRoot    = Resolve-Path "$PSScriptRoot\.."
$backendDir  = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$venvDir     = Join-Path $backendDir ".venv"
$venvPython  = Join-Path $venvDir   "Scripts\python.exe"
$backendEnv  = Join-Path $backendDir ".env"

# Tiny logging helpers (ASCII-only on purpose so the script parses cleanly
# regardless of the host's default file encoding).
$bar = ('-' * 72)
function Write-Section([string]$title) {
  Write-Host ""
  Write-Host $bar -ForegroundColor DarkGray
  Write-Host " $title" -ForegroundColor Cyan
  Write-Host $bar -ForegroundColor DarkGray
}
function Write-Ok([string]$m)   { Write-Host "  [ok]   $m" -ForegroundColor Green }
function Write-Skip([string]$m) { Write-Host "  [skip] $m" -ForegroundColor DarkGray }
function Write-Warn2([string]$m){ Write-Host "  [warn] $m" -ForegroundColor Yellow }
function Write-Info([string]$m) { Write-Host "  [..]   $m" -ForegroundColor Gray }
function Write-Fail([string]$m) { Write-Host "  [err]  $m" -ForegroundColor Red }

# 1. Prerequisites.
Write-Section "[1/6] Checking prerequisites"

function Get-Tool([string]$name) {
  return Get-Command $name -ErrorAction SilentlyContinue
}

# Discover a Python 3.11+ interpreter via the shared helper. This avoids the
# common Windows pitfall where `python` on PATH is a stale 2.7 or the Store
# alias stub; we try `py -3.12`, `py -3.11`, `py -3`, `python3`, `python` in
# order and accept the first that reports >= 3.11.
$pyInfo = Find-Python311Plus
if (-not $pyInfo.Found) {
  Write-Fail "No Python 3.11+ interpreter found. Tried:"
  foreach ($a in $pyInfo.Attempts) { Write-Host "           - $a" -ForegroundColor Red }
  Write-Fail "Install Python 3.11 or newer from https://www.python.org/downloads/"
  Write-Fail "Then close and re-open this terminal so PATH refreshes."
  exit 1
}
Write-Ok ("Python {0} (via '{1}')" -f $pyInfo.Version, $pyInfo.Invoke)

if (-not (Get-Tool node)) {
  Write-Fail "Node.js not found on PATH. Install Node.js 20+ from https://nodejs.org/"
  exit 1
}
try {
  $nodeVerRaw = (& node -v).Trim().TrimStart('v')
  $nodeMajor  = [int]($nodeVerRaw.Split('.')[0])
  if ($nodeMajor -lt 20) {
    Write-Fail "Node.js $nodeVerRaw is too old. Need Node 20 or newer."
    exit 1
  }
  Write-Ok "Node.js $nodeVerRaw"
} catch {
  Write-Fail "Could not determine Node version: $($_.Exception.Message)"
  exit 1
}

if (-not (Get-Tool npm)) {
  Write-Fail "npm not found on PATH (it should ship with Node.js)."
  exit 1
}
$npmVer = ((& npm -v) | Out-String).Trim()
Write-Ok "npm $npmVer"

# 2. Backend setup (venv + deps + DB + seed + initial model).
Write-Section "[2/6] Backend setup"

$needSetup = (-not (Test-Path $venvDir)) -or (-not (Test-Path $venvPython))
if ($needSetup) {
  Write-Info "venv missing - running scripts\setup.ps1 (this may take a few minutes on first run)..."
  & (Join-Path $PSScriptRoot "setup.ps1") -SkipFrontend
  if ($LASTEXITCODE -ne 0) {
    Write-Fail "setup.ps1 failed with exit code $LASTEXITCODE"
    exit 1
  }
  Write-Ok "Backend setup complete"
} else {
  Write-Skip "venv already exists at backend\.venv"
  if (-not (Test-Path $backendEnv)) {
    Copy-Item (Join-Path $backendDir ".env.example") $backendEnv
    Write-Ok "Created backend\.env from .env.example"
  }
}

# 3. Frontend deps.
Write-Section "[3/6] Frontend dependencies"

$nodeModules = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $nodeModules)) {
  Write-Info "node_modules missing - running npm install in frontend\..."
  Push-Location $frontendDir
  try {
    if (-not (Test-Path (Join-Path $frontendDir ".env.local"))) {
      Copy-Item (Join-Path $frontendDir ".env.example") (Join-Path $frontendDir ".env.local")
    }
    npm install --no-audit --no-fund --loglevel=error
    if ($LASTEXITCODE -ne 0) {
      Write-Fail "npm install failed with exit code $LASTEXITCODE"
      exit 1
    }
  } finally {
    Pop-Location
  }
  Write-Ok "Frontend deps installed"
} else {
  Write-Skip "frontend\node_modules already exists"
}

# 4. Ollama / LLM (non-fatal: never aborts the script).
Write-Section "[4/6] Local LLM (Ollama)"

# Resolve desired model: backend\.env > $env:LLM_MODEL > phi3.
$llmModel = $null
if (Test-Path $backendEnv) {
  $envLine = Select-String -Path $backendEnv -Pattern '^\s*LLM_MODEL\s*=\s*(.+)$' -ErrorAction SilentlyContinue
  if ($envLine) {
    $llmModel = $envLine.Matches[0].Groups[1].Value.Trim().Trim('"').Trim("'")
  }
}
if (-not $llmModel) { $llmModel = $env:LLM_MODEL }
if (-not $llmModel) { $llmModel = "phi3" }

$llmStatus = "fallback (no Ollama)"
$ollama    = Get-Tool ollama

function Test-OllamaUp {
  try {
    $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    return ($r.StatusCode -eq 200)
  } catch {
    return $false
  }
}

if (-not $ollama) {
  Write-Warn2 "Ollama is not installed - AI recommendations + chat will use deterministic offline fallbacks."
  Write-Warn2 "Install from https://ollama.com/download to enable the local LLM."
} else {
  Write-Ok "ollama CLI found"

  if (-not (Test-OllamaUp)) {
    Write-Info "Ollama server not responding - starting 'ollama serve' in the background..."
    try {
      Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden | Out-Null
    } catch {
      Write-Warn2 "Could not start 'ollama serve': $($_.Exception.Message)"
    }
    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline -and -not (Test-OllamaUp)) {
      Start-Sleep -Milliseconds 500
    }
  }

  if (Test-OllamaUp) {
    Write-Ok "Ollama server is up at http://localhost:11434"

    # Is the model already pulled? `ollama list` prints "model:tag ...".
    $hasModel = $false
    try {
      $list = (& ollama list 2>$null) | Out-String
      $hasModel = $list -match ("(?m)^\s*" + [regex]::Escape($llmModel) + "(:|\s)")
    } catch { $hasModel = $false }

    if ($hasModel) {
      Write-Skip "Model '$llmModel' is already pulled"
      $llmStatus = "running ($llmModel cached)"
    } else {
      Write-Info "Pulling model '$llmModel' (first time only - this can take a while)..."
      try {
        & ollama pull $llmModel
        if ($LASTEXITCODE -eq 0) {
          Write-Ok "Pulled '$llmModel'"
          $llmStatus = "running ($llmModel pulled)"
        } else {
          Write-Warn2 "ollama pull exited with code $LASTEXITCODE - continuing with offline fallback."
          $llmStatus = "fallback (pull failed)"
        }
      } catch {
        Write-Warn2 "ollama pull failed: $($_.Exception.Message). Continuing with offline fallback."
        $llmStatus = "fallback (pull failed)"
      }
    }
  } else {
    Write-Warn2 "Ollama server still unreachable - continuing with offline fallback."
    $llmStatus = "fallback (server unreachable)"
  }
}

# 5. Launch backend + frontend in their own windows.
Write-Section "[5/6] Launching backend + frontend"

# Backend command: cd into backend, run uvicorn from the venv (mirrors start_backend.ps1).
$backendCmd = "Set-Location -LiteralPath '$backendDir'; & '$venvPython' -m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort --reload"

# Frontend command (mirrors start_frontend.ps1). Backticks escape the inner $env reference.
$frontendCmd = "Set-Location -LiteralPath '$frontendDir'; if (-not `$env:VITE_API_BASE_URL) { `$env:VITE_API_BASE_URL = 'http://localhost:$BackendPort' }; npm run dev -- --port $FrontendPort --host"

Write-Info "Spawning backend window (uvicorn :$BackendPort)..."
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-NoProfile", "-Command", $backendCmd) | Out-Null
Write-Ok "Backend window launched"

Write-Info "Spawning frontend window (vite :$FrontendPort)..."
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-NoProfile", "-Command", $frontendCmd) | Out-Null
Write-Ok "Frontend window launched"

# 6. Wait for backend health, then open browser.
Write-Section "[6/6] Waiting for backend /health"

$backendUrl  = "http://localhost:$BackendPort"
$frontendUrl = "http://localhost:$FrontendPort"
$healthUrl   = "$backendUrl/api/v1/health"

$healthy = $false
for ($i = 1; $i -le 60; $i++) {
  try {
    $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($r.StatusCode -eq 200) { $healthy = $true; break }
  } catch {
    # not up yet
  }
  if ($i % 5 -eq 0) { Write-Info "still waiting... ($i s)" }
  Start-Sleep -Seconds 1
}

if ($healthy) {
  Write-Ok "Backend is healthy"
  if (-not $NoBrowser) {
    try {
      Start-Process $frontendUrl | Out-Null
      Write-Ok "Opened browser at $frontendUrl"
    } catch {
      Write-Warn2 "Could not open browser automatically: $($_.Exception.Message)"
    }
  }
} else {
  Write-Warn2 "Backend did not respond on /health within 60s - check the backend window for errors."
}

# Final summary box.
Write-Host ""
Write-Host $bar -ForegroundColor DarkGray
Write-Host "  AI Dropout Predictor - running" -ForegroundColor Green
Write-Host $bar -ForegroundColor DarkGray
Write-Host ("  Frontend (UI)    : {0}" -f $frontendUrl)        -ForegroundColor White
Write-Host ("  Backend  (API)   : {0}" -f $backendUrl)         -ForegroundColor White
Write-Host ("  Swagger / OpenAPI: {0}/docs" -f $backendUrl)    -ForegroundColor White
Write-Host ("  Health probe     : {0}" -f $healthUrl)          -ForegroundColor White
Write-Host ("  Local LLM        : {0}  (model: {1})" -f $llmStatus, $llmModel) -ForegroundColor White
Write-Host ""
Write-Host "  Default login    : admin@example.com  /  Admin@123" -ForegroundColor Yellow
Write-Host ""
Write-Host "  To stop the app, close the two PowerShell windows that were spawned" -ForegroundColor DarkGray
Write-Host "  (backend uvicorn + frontend vite)." -ForegroundColor DarkGray
Write-Host $bar -ForegroundColor DarkGray

exit 0
