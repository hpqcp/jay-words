# -*- coding: utf-8 -*-

Write-Host "=== back (FastAPI) ===" -ForegroundColor Green
$backend = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\backend"
    python -m uvicorn main:app --host 0.0.0.0 --port 18001
}
Start-Sleep 3

Write-Host "=== front (Vite) ===" -ForegroundColor Green
$frontend = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\frontend"
    npm run dev -- --host 0.0.0.0 --port 3000
}

Write-Host "`nstart ok" -ForegroundColor Green
Write-Host "   backend: http://localhost:18001" -ForegroundColor Cyan
Write-Host "   frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "`n Ctrl+C stop`n" -ForegroundColor Yellow

try {
    while ($true) { Start-Sleep 10 }
}
finally {
    Write-Host "`nstopping services..." -ForegroundColor Yellow
    Stop-Job $backend -ErrorAction SilentlyContinue
    Stop-Job $frontend -ErrorAction SilentlyContinue
    Remove-Job $backend -ErrorAction SilentlyContinue
    Remove-Job $frontend -ErrorAction SilentlyContinue
#    Write-Host "stopped" -ForegroundColor Green
}
