# LHM Engine Launcher
$ErrorActionPreference = "Stop"
Write-Host "Starting LHM Enhanced Engine..." -ForegroundColor Cyan
Write-Host ""
Set-Location "C:\Users\enock\Downloads"
& "C:\Users\enock\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py" --dry-run
Read-Host "Press Enter to exit"
