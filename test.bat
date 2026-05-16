@echo off
setlocal
cd /d "%~dp0"

echo [1/2] Running backend tests...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python environment not found at .venv\Scripts\python.exe
    exit /b 1
)
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 exit /b %errorlevel%

echo [2/2] Building frontend...
pushd frontend
npm.cmd run build
set BUILD_STATUS=%errorlevel%
popd
if not "%BUILD_STATUS%"=="0" exit /b %BUILD_STATUS%

echo [OK] Aegis validation passed.
