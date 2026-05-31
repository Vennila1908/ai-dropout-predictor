@echo off
REM Run the project's start script with a temporary execution policy bypass.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start_all.ps1"
if %ERRORLEVEL% neq 0 (
    echo.
    echo Serve failed. Check the output above for details.
    pause
)
