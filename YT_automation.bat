@echo off
echo ========================================
echo   YouTube Auto-Upload Automation
echo ========================================
echo.
echo Starting automation...
echo The system will monitor your folders and automatically upload videos to YouTube.
echo.
echo Press Ctrl+C to stop the automation.
echo.
echo ========================================
echo.

cd /d "%~dp0"
uv run youtube-automation

pause
