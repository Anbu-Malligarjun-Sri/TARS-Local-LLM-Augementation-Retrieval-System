$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeFolder = Join-Path $projectRoot '.runtime'
$pythonPath = Join-Path (Split-Path -Parent $projectRoot) '.venv\Scripts\python.exe'
$pidFile = Join-Path $runtimeFolder 'coding-worker.json'
New-Item -ItemType Directory -Force -Path $runtimeFolder | Out-Null
if (Test-Path -LiteralPath $pidFile) {
    $record = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
    $existing = Get-CimInstance Win32_Process -Filter "ProcessId = $($record.pid)" -ErrorAction SilentlyContinue
    if ($existing -and $existing.CommandLine -like '*-m src.jobs.worker*' -and $existing.CommandLine.Contains($pythonPath)) {
        Write-Output "TARS coding worker already running (PID $($record.pid))."
        return
    }
}
$worker = Start-Process -FilePath $pythonPath -ArgumentList '-m','src.jobs.worker' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeFolder 'coding-worker.log') -RedirectStandardError (Join-Path $runtimeFolder 'coding-worker-error.log')
@{pid=$worker.Id; started_at=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $pidFile
Write-Output "TARS coding worker started (PID $($worker.Id)); jobs still require individual approval and a passing sandbox preflight."
