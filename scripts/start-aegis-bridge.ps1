Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$LocalDir = Join-Path $RepoRoot ".local"
$TokenPath = Join-Path $LocalDir "aegis-bridge-token.txt"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BridgeUrl = "http://127.0.0.1:8765"

function New-AegisBridgeToken {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }
    return ([Convert]::ToBase64String($bytes)).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    Write-Host "[ERROR] Python virtual environment not found:" -ForegroundColor Red
    Write-Host "        $PythonPath"
    Write-Host "Create the Aegis .venv before starting the bridge."
    exit 1
}

if (-not (Test-Path -LiteralPath $LocalDir -PathType Container)) {
    New-Item -ItemType Directory -Path $LocalDir | Out-Null
}

if (-not (Test-Path -LiteralPath $TokenPath -PathType Leaf)) {
    $token = New-AegisBridgeToken
    Set-Content -LiteralPath $TokenPath -Value $token -NoNewline -Encoding ASCII
    Write-Host "[OK] Created local bridge token file."
}
else {
    $token = (Get-Content -LiteralPath $TokenPath -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($token)) {
        Write-Host "[ERROR] Bridge token file exists but is empty:" -ForegroundColor Red
        Write-Host "        $TokenPath"
        Write-Host "Delete it and rerun this script to generate a new token."
        exit 1
    }
}

$env:AEGIS_BRIDGE_TOKEN = $token

Write-Host "==================================================="
Write-Host "Aegis Read-Only ChatGPT Bridge"
Write-Host "==================================================="
Write-Host "Bridge URL:       $BridgeUrl"
Write-Host "Token file:       $TokenPath"
Write-Host "Auth header:      X-Aegis-Bridge-Token"
Write-Host "OpenAPI schema:   docs\aegis-read-only-bridge-openapi.yaml"
Write-Host ""
Write-Host "Do not share the token or commit .local files."
Write-Host "Custom GPT Actions need an HTTPS tunnel URL, not localhost."
Write-Host "Use scripts\show-aegis-bridge-token.ps1 only when you intentionally need to copy the token."
Write-Host ""
Write-Host "Starting bridge..."
Write-Host "Press Ctrl+C to stop."
Write-Host "==================================================="

Set-Location -LiteralPath $RepoRoot
& $PythonPath -m aegis.read_only_bridge
exit $LASTEXITCODE
