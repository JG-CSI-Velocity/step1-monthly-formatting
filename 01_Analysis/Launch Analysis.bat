@echo off
title CSI Velocity - ARS Analysis
color 0A

echo.
echo ======================================================================
echo   CSI VELOCITY - ARS Analysis Pipeline
echo ======================================================================
echo.
echo   [1] Launch UI (browser-based dashboard)
echo   [2] Run from command line (specify client directly)
echo.
set /p choice="   Select (1 or 2): "

if "%choice%"=="1" goto ui
if "%choice%"=="2" goto cli
goto ui

:ui
echo.
echo   Starting UI server...
echo   (Your browser will open automatically)
echo   (Close this window or press Ctrl+C to stop)
echo.

cd /d "%~dp0.."

:: Install dependencies if needed
pip install -r requirements.txt >nul 2>&1

:: Launch the FastAPI UI
python ui\app.py
goto end

:cli
echo.
set /p month="   Month (e.g. 2026.03): "
set /p csm="   CSM name (e.g. JamesG): "
set /p client="   Client ID (e.g. 1200): "
echo.
echo   Running analysis for client %client%, month %month%...
echo.

cd /d "%~dp0"
python run.py --month %month% --csm %csm% --client %client%

echo.
pause
goto end

:end
