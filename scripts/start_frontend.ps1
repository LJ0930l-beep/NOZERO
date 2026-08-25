param(
  [int]$Port = 3000
)

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $projectRoot "frontend")
npm run dev -- --port $Port
