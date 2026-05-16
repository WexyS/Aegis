@echo off
setlocal
cd /d "%~dp0"

echo [INFO] Delegating debug launch to launch_aegis.bat...
call launch_aegis.bat
