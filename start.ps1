Write-Host "=== 启动后端 (FastAPI) ===" -ForegroundColor Green
$backend = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\backend"
    python -m uvicorn main:app --host 0.0.0.0 --port 18001
}
Start-Sleep 3

Write-Host "=== 启动前端 (Vite) ===" -ForegroundColor Green
$frontend = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\frontend"
    npx vite --host 0.0.0.0 --port 3000
}

Write-Host "`n✅ 服务已启动！" -ForegroundColor Green
Write-Host "   前端: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   后端: http://localhost:8000" -ForegroundColor Cyan
Write-Host "`n按 Ctrl+C 停止服务`n" -ForegroundColor Yellow

try {
    # Keep script running
    while ($true) { Start-Sleep 10 }
}
finally {
    Write-Host "`n正在停止服务..." -ForegroundColor Yellow
    Stop-Job $backend -ErrorAction SilentlyContinue
    Stop-Job $frontend -ErrorAction SilentlyContinue
    Remove-Job $backend -ErrorAction SilentlyContinue
    Remove-Job $frontend -ErrorAction SilentlyContinue
    Write-Host "服务已停止" -ForegroundColor Green
}
