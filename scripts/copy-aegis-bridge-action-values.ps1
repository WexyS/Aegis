Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NgrokUrlScriptPath = Join-Path $ScriptDir "show-aegis-ngrok-url.ps1"
$OpenApiPath = "docs\aegis-read-only-bridge-openapi.yaml"
$HeaderName = "X-Aegis-Bridge-Token"

try {
    $ngrokOutput = & $NgrokUrlScriptPath 2>$null
    $ngrokUrl = ($ngrokOutput | Where-Object { $_ -like "https://*" } | Select-Object -First 1)
}
catch {
    $ngrokUrl = $null
}

if ([string]::IsNullOrWhiteSpace($ngrokUrl)) {
    Write-Host "Run ngrok http 8765 or start-aegis-bridge-and-ngrok.bat first."
    exit 1
}

$summary = @"
Aegis Custom GPT Action setup

Server URL:
$ngrokUrl

Auth header:
$HeaderName

OpenAPI schema:
$OpenApiPath

Token:
Paste manually from scripts\show-aegis-bridge-token.ps1. This helper does not print the token.
"@

Write-Host $summary

try {
    Set-Clipboard -Value $summary
    Write-Host "Copied setup summary to clipboard."
}
catch {
    Write-Host "Clipboard copy unavailable; copy the setup summary manually."
}
