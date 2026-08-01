@echo off
chcp 65001 >nul
title Stop All Services

echo Stopping all services...

REM Stop backend
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Stop localtunnel (node processes started by lt)
taskkill /fi "WINDOWTITLE eq Tunnel*" /f >nul 2>&1

echo All services stopped.
timeout /t 2 /nobreak >nul
