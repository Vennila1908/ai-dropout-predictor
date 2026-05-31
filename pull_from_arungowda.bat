@echo off
REM Pull latest changes from the upstream repository while auto-stashing local modifications.
cd /d "%~dp0"
cd /d "%~dp0"
git pull --autostash https://github.com/arungowda-p/ai-dropout-predictor.git main
if %ERRORLEVEL% neq 0 (
    echo.
    echo Pull failed. Check the output above for details.
    pause
)
