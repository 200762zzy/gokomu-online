@echo off
chcp 936 >nul
title Gomoku Online

echo ============================================
echo   Gomoku Online - Production Mode
echo ============================================
echo.

cd /d "%~dp0backend"
echo Starting server at http://localhost:8000
echo Frontend + API are served on the same port.
echo.
python run.py

pause
