# register-workloads.ps1 - Register per-service SPIFFE entries
# -------------------------------------------------------------
# Usage (from project root):
#   powershell -ExecutionPolicy Bypass -File .\spire\scripts\register-workloads.ps1
#
# Uses the docker WorkloadAttestor (enabled in spire/agent/agent.conf).
# Each service container is identified by the label `com.guardians.service`
# which is set in docker-compose.yml.
#
# IMPORTANT: This script REPLACES any previous entries. Run it after every
# agent.conf / compose change to keep selectors consistent.
$ErrorActionPreference = "Continue"

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$SPIFFE_DOMAIN = "spiffe://guardians.local"
$AGENT_SPIFFE  = "$SPIFFE_DOMAIN/agent/docker"

# Service name === label value === SPIFFE ID suffix
$services = @("gateway", "auth", "profile", "grades", "enrollments", "registrations")

Write-Host "=== Guardians Zero-Trust Portal: Workload Registration ===" -ForegroundColor Cyan

# 1) 기존 service entry 모두 삭제 (selector 가 바뀌었을 수 있어 깨끗하게 다시)
Write-Host ""
Write-Host "--- Cleaning up previous service entries ---" -ForegroundColor Yellow
$existing = docker compose exec -T spire-server /opt/spire/bin/spire-server entry show 2>&1 | Out-String
$entryIdRegex = [regex] 'Entry ID\s*:\s*([0-9a-f-]+)\s*\nSPIFFE ID\s*:\s*spiffe://guardians\.local/service/'
foreach ($m in $entryIdRegex.Matches($existing)) {
    $id = $m.Groups[1].Value
    Write-Host "  - Deleting entry $id"
    docker compose exec -T spire-server `
        /opt/spire/bin/spire-server entry delete -entryID $id 2>&1 | Out-String | Write-Host
}

# 2) docker:label selector 로 서비스별 entry 등록
Write-Host ""
Write-Host "--- Registering per-service entries (docker label selector) ---" -ForegroundColor Yellow
foreach ($name in $services) {
    $spiffeId = "$SPIFFE_DOMAIN/service/$name"
    $labelSel = "docker:label:com.guardians.service:$name"
    Write-Host "  - $spiffeId  ($labelSel)"

    docker compose exec -T spire-server `
        /opt/spire/bin/spire-server entry create `
        -parentID $AGENT_SPIFFE `
        -spiffeID $spiffeId `
        -selector $labelSel `
        -ttl 3600 2>&1 | Out-String | Write-Host
}

Write-Host ""
Write-Host "=== Registered Entries ===" -ForegroundColor Green
docker compose exec -T spire-server /opt/spire/bin/spire-server entry show 2>&1 | Out-String | Write-Host
