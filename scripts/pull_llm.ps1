[CmdletBinding()]
param([string]$Model = "phi3")
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  Write-Host "Ollama is not installed. Get it from https://ollama.com/download" -ForegroundColor Yellow
  exit 1
}
Write-Host "Pulling Ollama model: $Model" -ForegroundColor Cyan
ollama pull $Model
