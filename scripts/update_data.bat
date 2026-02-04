@echo off
REM Portal IQ Data Update Script
REM Run this weekly during season, monthly off-season

echo ============================================
echo    Portal IQ Data Update
echo ============================================
echo.

REM Change to project directory
cd /d "%~dp0\.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Run the update script
echo Running data update...
echo.
python scripts/update_portal_iq_data.py %*

echo.
echo ============================================
echo    Update Complete!
echo ============================================
echo.
echo Check the logs folder for detailed results.
echo.
pause
