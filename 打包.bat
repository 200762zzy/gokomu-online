@echo off
chcp 65001 >nul
title Gomoku Online - Packing

echo ============================================
echo   Gomoku Online - Build Distribution
echo ============================================
echo.

cd /d "%~dp0frontend"
echo [1/3] Building frontend...
call npm install --silent
call npm run build

cd /d "%~dp0"
echo [2/3] Installing PyInstaller...
pip install pyinstaller -q

echo [3/3] Packing backend into EXE...
:: Clean previous exe
if exist "%~dp0GomokuOnline.exe" del /q "%~dp0GomokuOnline.exe"
cd /d "%~dp0backend"
pyinstaller --onefile --name GomokuOnline run.py ^
  --add-data "..\frontend\dist;frontend_dist" ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.loops.asyncio ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  --hidden-import httpx ^
  --hidden-import aiosqlite ^
  --distpath ".." ^
  REM --noconsole

cd /d "%~dp0"
if exist "GomokuOnline.exe" (
    :: Clean up PyInstaller build artifacts
    if exist "backend\build" rmdir /s /q "backend\build"
    if exist "backend\GomokuOnline.spec" del /q "backend\GomokuOnline.spec"

    echo.
    echo ============================================
    echo   Done! Single EXE at: %~dp0GomokuOnline.exe
    echo ============================================
    dir GomokuOnline.exe
) else (
    echo [ERROR] Build failed!
)
pause
