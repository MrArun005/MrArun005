# Kaggriculture live status — run from any terminal, no Claude needed:
#   powershell -File status.ps1          (or .\status.ps1 from the repo folder)
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

Write-Host "=== KAGGLE LADDER (live ratings) ===" -ForegroundColor Cyan
& C:\kv\Scripts\kaggle.exe competitions submissions kaggriculture 2>$null |
    Select-Object -First 8 | ForEach-Object {
        $line = $_ -replace 'SubmissionStatus\.', ''
        if ($line.Length -gt 150) { $line = $line.Substring(0, 95) + '...' + $line.Substring($line.Length - 30) }
        Write-Host $line
    }

Write-Host "`n=== LOCAL PROCESSES ===" -ForegroundColor Cyan
$py = @(Get-Process python -ErrorAction SilentlyContinue)
if ($py.Count) {
    Write-Host "$($py.Count) python process(es) running (started: $(($py | ForEach-Object { $_.StartTime.ToString('HH:mm') }) -join ', '))"
} else { Write-Host "nothing running" }

Write-Host "`n=== ACTIVE LOGS (latest lines) ===" -ForegroundColor Cyan
foreach ($log in @("tune_v4.log", "harvest.log")) {
    if (Test-Path $log) {
        $item = Get-Item $log
        $age = [int]((Get-Date) - $item.LastWriteTime).TotalMinutes
        Write-Host "-- $log (updated ${age}m ago)" -ForegroundColor Yellow
        Get-Content $log -Tail 3
    }
}
if (Test-Path "dataset\index.json") {
    Write-Host "`ndataset index: READY ($([math]::Round((Get-Item dataset\index.json).Length/1KB)) KB)" -ForegroundColor Green
} else { Write-Host "`ndataset index: not built yet" }

Write-Host "`n=== GIT ===" -ForegroundColor Cyan
git log --oneline -1
git status -sb | Select-Object -First 1
