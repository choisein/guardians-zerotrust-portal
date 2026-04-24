# bootstrap-agent.ps1 - SPIRE Agent bootstrap (Windows / PowerShell)
# -------------------------------------------------------------------
# Generates a Join Token from SPIRE Server and writes it to .env as
# JOIN_TOKEN so docker-compose can inject it into the spire-agent container.
#
# Usage (from project root):
#   powershell -ExecutionPolicy Bypass -File .\spire\scripts\bootstrap-agent.ps1

# Do NOT stop on stderr from native commands (docker prints warnings to stderr)
$ErrorActionPreference = "Continue"

# Force UTF-8 console output (avoids mojibake in Windows PowerShell 5.1)
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

Write-Host "=== SPIRE Agent Bootstrap ===" -ForegroundColor Cyan

# --- 0) Make sure .env exists and has a JOIN_TOKEN line ---
# (docker compose warns if referenced variable is missing; pre-seeding silences it)
$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
    Set-Content -Path $envPath -Value "JOIN_TOKEN=" -Encoding ascii
}
$envLines = Get-Content $envPath
if (-not ($envLines | Where-Object { $_ -match '^\s*JOIN_TOKEN\s*=' })) {
    Add-Content -Path $envPath -Value "JOIN_TOKEN="
}

# --- 1) Verify spire-server is running ---
Write-Host "[1/3] Checking spire-server status..."
$psOutput = (docker compose ps spire-server 2>&1 | Out-String)
if ($psOutput -notmatch "running|Up") {
    Write-Host "spire-server is NOT running. Start it first:" -ForegroundColor Yellow
    Write-Host "  docker compose up -d spire-server"
    Write-Host ""
    Write-Host "Current status:"
    Write-Host $psOutput
    exit 1
}

# --- 2) Generate Join Token ---
Write-Host "[2/3] Generating Join Token..."
$raw = (docker compose exec -T spire-server `
    /opt/spire/bin/spire-server token generate `
    -spiffeID spiffe://guardians.local/agent/docker 2>&1 | Out-String)

# Output looks like: "Token: abcdef-1234-..."
$match = [regex]::Match($raw, 'Token:\s*([^\s]+)')
if (-not $match.Success) {
    Write-Host "Failed to extract token. Raw output:" -ForegroundColor Red
    Write-Host $raw
    exit 1
}
$token = $match.Groups[1].Value.Trim()
Write-Host "      Token: $token"

# --- 3) Write token to .env ---
Write-Host "[3/3] Writing JOIN_TOKEN to .env..."
$newLines = @()
foreach ($line in (Get-Content $envPath)) {
    if ($line -match '^\s*JOIN_TOKEN\s*=') { continue }
    $newLines += $line
}
$newLines += "JOIN_TOKEN=$token"
Set-Content -Path $envPath -Value $newLines -Encoding ascii

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  docker compose up -d spire-agent"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\spire\scripts\register-workloads.ps1"
