@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_release.ps1" -Mode both %*
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Review the PowerShell messages above.
) else (
    echo.
    echo DONE. Check the release folder.
)
pause
