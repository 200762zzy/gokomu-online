@echo off
chcp 65001 >nul
title Gomoku Online Launcher

echo ============================================
echo   Gomoku Online - One-Click Launcher
echo ============================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

cd /d "%~dp0backend"
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt -q

cd /d "%~dp0frontend"
if not exist "dist\index.html" (
    echo [2/4] Building frontend...
    call npm install --silent
    call npm run build
) else (
    echo [2/4] Frontend already built, skipping
)

cd /d "%~dp0backend"
echo [3/4] Starting server...
start "Gomoku-Server" python run.py

echo [4/4] Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:8000

echo.
echo Server is running! Share the Network IP shown in the server window.
echo Press any key to stop the server...
pause

taskkill /f /fi "WINDOWTITLE eq Gomoku-Server" >nul 2>&1
