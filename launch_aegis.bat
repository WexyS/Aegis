@echo off
setlocal EnableDelayedExpansion
title Aegis Runtime Orchestrator

echo [0/6] Cleaning up ghost processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root = (Resolve-Path '%~dp0').Path; Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('node.exe','electron.exe') -and $_.CommandLine -like ('*' + $root + '*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
taskkill /F /IM electron.exe /T >nul 2>&1
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "0.0.0.0:3000"') DO taskkill /F /PID %%T >nul 2>&1
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "127.0.0.1:3000"') DO taskkill /F /PID %%T >nul 2>&1
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "[::1]:3000"') DO taskkill /F /PID %%T >nul 2>&1
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "0.0.0.0:8400"') DO taskkill /F /PID %%T >nul 2>&1
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "127.0.0.1:8400"') DO taskkill /F /PID %%T >nul 2>&1
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "[::1]:8400"') DO taskkill /F /PID %%T >nul 2>&1

echo [1/6] Initializing Aegis Environment...
cd /d "%~dp0"

echo [2/6] Checking LM Studio / Local Model...
:: This is a health check for the local LLM running on standard port 1234 or similar.
curl -s http://localhost:1234/v1/models > nul
if %errorlevel% neq 0 (
    echo [WARN] LM Studio not detected on port 1234. Aegis may start in Passive Mode.
) else (
    echo [OK] Local LLM is accessible.
)

echo [3/6] Starting Runtime Backend (Uvicorn)...
if exist .venv (
    start "Aegis Backend" cmd /c ".\.venv\Scripts\python src\aegis\main.py"
    echo [OK] Backend spawned.
) else (
    echo [ERROR] Python environment .venv not found.
)

echo [4/6] Booting Aegis Frontend ^& Electron...
cd frontend
if not exist node_modules (
    echo [INFO] Installing frontend dependencies...
    npm install
)

:: Some automation shells export ELECTRON_RUN_AS_NODE=1. That makes
:: electron.exe run as Node.js and prevents BrowserWindow from starting.
set ELECTRON_RUN_AS_NODE=

:: Using concurrently to run Next.js and Electron together
echo [5/6] Spawning UI processes...
start "Aegis UI" cmd /c "npm run electron:dev"

echo [6/6] Healthcheck ^& Auto-open...
:: We rely on wait-on inside npm run dev to open Electron, but we can also do a ping loop here if needed.
echo [OK] All systems go. Aegis Mission Control is Online.
echo ===================================================
echo [!] Keep this terminal open to monitor orchestrator logs.
echo ===================================================

:: Tail-like keepalive
:loop
ping localhost -n 60 > nul
goto loop
