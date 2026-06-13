Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$TokenPath = Join-Path $RepoRoot ".local\aegis-bridge-token.txt"

if (-not (Test-Path -LiteralPath $TokenPath -PathType Leaf)) {
    Write-Host "[ERROR] Bridge token file not found:" -ForegroundColor Red
    Write-Host "        $TokenPath"
    Write-Host "Run scripts\start-aegis-bridge.bat first to create it."
    exit 1
}

Write-Host "This will print the local Aegis bridge token."
Write-Host "Only paste it into your own Custom GPT Action auth settings."
Write-Host "Do not share it in prompts, screenshots, docs, commits, or issue comments."
$confirmation = Read-Host "Type SHOW to print the token"

if ($confirmation -ne "SHOW") {
    Write-Host "Token display cancelled."
    exit 1
}

Write-Host ""
Write-Host "X-Aegis-Bridge-Token:"
Get-Content -LiteralPath $TokenPath -Raw
