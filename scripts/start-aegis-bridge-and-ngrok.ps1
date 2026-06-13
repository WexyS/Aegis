Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$TokenPath = Join-Path $RepoRoot ".local\aegis-bridge-token.txt"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BridgeScriptPath = Join-Path $ScriptDir "start-aegis-bridge.ps1"
$NgrokUrlScriptPath = Join-Path $ScriptDir "show-aegis-ngrok-url.ps1"
$BridgeUrl = "http://127.0.0.1:8765"
$NgrokCommand = Get-Command ngrok -ErrorAction SilentlyContinue

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    Write-Host "[ERROR] Python virtual environment not found:" -ForegroundColor Red
    Write-Host "        $PythonPath"
    Write-Host "Create the Aegis .venv before starting the bridge."
    exit 1
}

& $BridgeScriptPath -PrepareOnly -Quiet

if (-not (Test-Path -LiteralPath $TokenPath -PathType Leaf)) {
    Write-Host "[ERROR] Bridge token file was not created:" -ForegroundColor Red
    Write-Host "        $TokenPath"
    exit 1
}

$token = (Get-Content -LiteralPath $TokenPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "[ERROR] Bridge token file is empty:" -ForegroundColor Red
    Write-Host "        $TokenPath"
    Write-Host "Delete it and rerun scripts\start-aegis-bridge.bat to generate a new token."
    exit 1
}
$env:AEGIS_BRIDGE_TOKEN = $token

Write-Host "==================================================="
Write-Host "Aegis Read-Only ChatGPT Bridge + Ngrok"
Write-Host "==================================================="
Write-Host "Local bridge URL: $BridgeUrl"
Write-Host "Token file:       $TokenPath"
Write-Host "Auth header:      X-Aegis-Bridge-Token"
Write-Host "OpenAPI schema:   docs\aegis-read-only-bridge-openapi.yaml"
Write-Host ""
Write-Host "Use scripts\show-aegis-bridge-token.ps1 to copy the token."
Write-Host "Use scripts\show-aegis-ngrok-url.ps1 to copy the ngrok HTTPS URL after ngrok starts."
Write-Host "Custom GPT Actions need the ngrok HTTPS URL in OpenAPI servers.url."
Write-Host "Do not share the token or ngrok URL."
Write-Host "==================================================="

Set-Location -LiteralPath $RepoRoot

Write-Host "[1/2] Starting read-only bridge in a separate window..."
Start-Process -FilePath $PythonPath `
    -ArgumentList @("-m", "aegis.read_only_bridge") `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Normal `
    -PassThru | Out-Null

if ($null -eq $NgrokCommand) {
    Write-Host ""
    Write-Host "[WARN] ngrok was not found on PATH." -ForegroundColor Yellow
    Write-Host "The bridge is still starting locally at $BridgeUrl."
    Write-Host "Install/configure ngrok, then run:"
    Write-Host "    ngrok http 8765"
    Write-Host "Then run:"
    Write-Host "    scripts\show-aegis-ngrok-url.ps1"
    exit 0
}

Write-Host "[2/2] Starting ngrok tunnel in a separate window..."
Start-Process -FilePath $NgrokCommand.Source `
    -ArgumentList @("http", "8765") `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Normal `
    -PassThru | Out-Null

Write-Host ""
Write-Host "Wait a few seconds for ngrok to initialize, then run:"
Write-Host "    $NgrokUrlScriptPath"
Write-Host ""
Write-Host "Stop bridge/ngrok by closing their windows or pressing Ctrl+C in each process."
exit 0
