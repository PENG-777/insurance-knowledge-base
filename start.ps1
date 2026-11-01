$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root "fastapi\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "未找到后端虚拟环境：$python" -ForegroundColor Red
    Write-Host "请先执行：cd fastapi; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

$fastapi = Join-Path $root "fastapi"
$vue = Join-Path $root "vue"

Write-Host "启动后端 FastAPI  http://127.0.0.1:8000" -ForegroundColor Cyan
Start-Process -FilePath $python -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $fastapi

Write-Host "启动前端 Vite     http://127.0.0.1:5173" -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm run dev") -WorkingDirectory $vue

Write-Host "已在新窗口启动前后端，首次启动会自动建表并写入演示数据。" -ForegroundColor Green
Write-Host "关闭对应命令行窗口即可停止服务。" -ForegroundColor DarkGray
