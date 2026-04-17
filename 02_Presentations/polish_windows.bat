@echo off
setlocal

REM One-click polish launcher for Windows.
REM Drops decks in .\decks_to_polish\ -- double-click this file to polish them all.

cd /d "%~dp0"

if not exist "decks_to_polish" mkdir "decks_to_polish"

REM Check Python is available
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found on PATH.
    echo Install Python 3.12+ from python.org and re-run.
    pause
    exit /b 1
)

REM Count decks
set count=0
for %%f in ("decks_to_polish\*.pptx") do set /a count+=1

if %count%==0 (
    echo No .pptx files found in decks_to_polish\
    echo.
    echo 1. Drop your decks into:
    echo    %cd%\decks_to_polish\
    echo 2. Double-click polish_windows.bat again.
    echo.
    pause
    exit /b 0
)

echo Polishing %count% deck^(s^)...
python polish.py --batch "decks_to_polish" --out "polished" --apply
if errorlevel 1 (
    echo.
    echo Polish failed. See errors above.
    pause
    exit /b 1
)

echo.
echo Done. Opening polished\ folder...
start "" "polished"
pause
