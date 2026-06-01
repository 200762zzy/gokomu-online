@echo off
chcp 936 >nul
echo ============================================
echo   Gomoku Online - Local Two Player
echo ============================================
echo.

cd /d "%~dp0frontend"
echo Starting frontend...
start "Gomoku-Frontend" cmd /c "npm run dev"

cd /d "%~dp0"
echo.
echo Frontend: http://localhost:5173
echo.
echo Press any key to stop...
pause

taskkill /f /fi "WINDOWTITLE eq Gomoku-Frontend" >nul 2>&1
