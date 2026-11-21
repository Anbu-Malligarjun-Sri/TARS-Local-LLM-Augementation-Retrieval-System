$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeFolder = Join-Path $projectRoot '.runtime'
$pythonPath = Join-Path (Split-Path -Parent $projectRoot) '.venv\Scripts\python.exe'
$nodePath = (Get-Command node).Source
New-Item -ItemType Directory -Force -Path $runtimeFolder | Out-Null
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) {
    throw 'Configure .env first using docs/PHASE_1_SETUP.md.'
}
lms daemon up --json
lms server start --port 1234 --bind 127.0.0.1
$loaded = lms ps | Out-String
if ($loaded -notmatch [regex]::Escape('qwen/qwen3.5-9b')) {
    lms load qwen/qwen3.5-9b --context-length 8192 --yes
}
if ($loaded -notmatch [regex]::Escape('text-embedding-nomic-embed-text-v1.5')) {
    lms load text-embedding-nomic-embed-text-v1.5 --yes
}
if (-not (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','src.interfaces.api:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeFolder 'backend.log') -RedirectStandardError (Join-Path $runtimeFolder 'backend-error.log')
}
if (-not (Get-NetTCPConnection -State Listen -LocalPort 8081 -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $nodePath -ArgumentList 'node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','8081','--strictPort' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeFolder 'frontend.log') -RedirectStandardError (Join-Path $runtimeFolder 'frontend-error.log')
}
# A single-use fragment ticket is exchanged for an HttpOnly cookie, then removed.
# The owner token is never placed in a browser URL.
& (Join-Path $PSScriptRoot 'start-coding-worker.ps1')
$launchUrl = & $pythonPath -m src.interfaces.launch
Write-Output "TARS launch link (single use; valid for ten minutes): $launchUrl"
Start-Process $launchUrl -WindowStyle Hidden
