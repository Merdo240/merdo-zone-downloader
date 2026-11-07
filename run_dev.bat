@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "app\merdo_zone_downloader.py"
) else (
    python "app\merdo_zone_downloader.py"
)
pause
