@echo off
chcp 65001 >nul
title GONGKAOXING - Backend + LocalTunnel

cd /d "%~dp0"

echo ============================================
echo   GONGKAOXING - Backend + Tunnel Start
echo ============================================
echo.

REM Kill existing backend on port 8000
echo [0] Cleaning port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM Start backend
echo [1] Starting backend (port 8000)...
start "Backend" /min cmd /c "C:\Users\30709\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\vm\tools\python\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000" /d "%~dp0backend"

timeout /t 4 /nobreak >nul

REM Verify backend
echo [2] Checking backend...
set API_OK=0
for /f "delims=" %%i in ('curl -s http://localhost:8000/api/health 2^>nul') do set API_OK=1
if "%API_OK%"=="1" (
    echo     Backend OK
) else (
    echo     Backend may still be starting...
)

REM Start localtunnel
echo [3] Starting localtunnel...
start "Tunnel" cmd /c "C:\Users\30709\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\vm\tools\node\lt.cmd --port 8000"

echo.
echo ============================================
echo   Waiting for tunnel URL...
echo   Check the "Tunnel" window for your public URL
echo ============================================
echo.
echo   Local:  http://localhost:8000
echo.
echo Press any key to test tunnel...
pause >nul

echo.
echo [4] Checking tunnel (may take a few seconds)...
set LT_URL=
for /f "tokens=2 delims=:" %%a in ('curl -s https://lt.local-tunnel.dev 2^>nul ^| findstr "your url"') do (
    set "LT_URL=%%a"
)
if defined LT_URL (
    echo     Tunnel: https:%LT_URL%
) else (
    echo     Look at the Tunnel window for your URL
)

echo.
pause
