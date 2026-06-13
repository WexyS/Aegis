@echo off
setlocal
title Aegis Read-Only ChatGPT Bridge

set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-aegis-bridge.ps1"
set "AEGIS_BRIDGE_EXIT=%ERRORLEVEL%"

if not "%AEGIS_BRIDGE_EXIT%"=="0" (
    echo.
    echo [ERROR] Aegis read-only bridge exited with code %AEGIS_BRIDGE_EXIT%.
    echo Press any key to close this window.
    pause >nul
    exit /b %AEGIS_BRIDGE_EXIT%
)

exit /b 0
