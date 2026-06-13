Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$NgrokApiUrl = "http://127.0.0.1:4040/api/tunnels"

try {
    $response = Invoke-RestMethod -Uri $NgrokApiUrl -Method Get -TimeoutSec 3
}
catch {
    Write-Host "Run ngrok http 8765 or start-aegis-bridge-and-ngrok.bat first."
    exit 1
}

$httpsTunnel = @($response.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1)
if (-not $httpsTunnel -or [string]::IsNullOrWhiteSpace($httpsTunnel[0].public_url)) {
    Write-Host "Run ngrok http 8765 or start-aegis-bridge-and-ngrok.bat first."
    exit 1
}

$url = [string]$httpsTunnel[0].public_url
Write-Host "Aegis bridge ngrok HTTPS URL:"
Write-Host $url
Write-Host ""
Write-Host "Paste this URL into docs\aegis-read-only-bridge-openapi.yaml as servers.url for Custom GPT Actions."
Write-Host "Auth header remains: X-Aegis-Bridge-Token"
Write-Host "This helper does not print or expose the bridge token."
Write-Host "This helper does not print the token."

try {
    Set-Clipboard -Value $url
    Write-Host "Copied ngrok URL to clipboard."
}
catch {
    Write-Host "Clipboard copy unavailable; copy the URL manually."
}
