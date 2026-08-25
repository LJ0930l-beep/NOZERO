$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

python -m ruff check backend ai pose scripts
python -m pytest -q
Set-Location (Join-Path $projectRoot "frontend")
npm run test
npx tsc --noEmit
npm run lint
npm run build
