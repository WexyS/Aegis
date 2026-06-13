@echo off
setlocal
title Aegis Read-Only Bridge + Ngrok

set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-aegis-bridge-and-ngrok.ps1"
set "AEGIS_BRIDGE_NGROK_EXIT=%ERRORLEVEL%"

if not "%AEGIS_BRIDGE_NGROK_EXIT%"=="0" (
    echo.
    echo [ERROR] Aegis bridge/ngrok launcher exited with code %AEGIS_BRIDGE_NGROK_EXIT%.
    echo Press any key to close this window.
    pause >nul
    exit /b %AEGIS_BRIDGE_NGROK_EXIT%
)

exit /b 0
