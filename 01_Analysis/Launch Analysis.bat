@echo off
title CSI Velocity - ARS Analysis
color 0A

:: Go to repo root (one level up from 01_Analysis)
cd /d "%~dp0.."

echo.
echo ======================================================================
echo   CSI VELOCITY - ARS Analysis Pipeline
echo   Starting UI at http://localhost:8000
echo ======================================================================
echo.

:: Find app.py in whichever UI folder exists
if exist "05_UI\app.py" (
    set UI_PATH=05_UI\app.py
) else if exist "ui\app.py" (
    set UI_PATH=ui\app.py
) else (
    echo   ERROR: Cannot find app.py
    echo   Looked in: 05_UI\app.py and ui\app.py
    echo   Current directory: %cd%
    echo.
    dir /b
    echo.
    pause
    exit /b 1
)

echo   Found: %UI_PATH%
echo.

:: Launch browser first, then start server
start http://localhost:8000

:: Start the FastAPI server (blocks until closed)
python %UI_PATH%

echo.
pause
