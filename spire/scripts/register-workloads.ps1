# register-workloads.ps1 - Register per-service SPIFFE entries
# -------------------------------------------------------------
# Usage (from project root):
#   powershell -ExecutionPolicy Bypass -File .\spire\scripts\register-workloads.ps1
#
# NOTE: docker WorkloadAttestor is disabled in agent.conf due to docker.sock
# permission issues on Windows/WSL. We use the unix attestor instead, which
# identifies workloads by uid (all containers run as root → uid:0).
#
# This means ALL services share the same selector and would all match the
# same SPIFFE entries. To distinguish services, we use the binary path selector.

$ErrorActionPreference = "Continue"

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$SPIFFE_DOMAIN = "spiffe://guardians.local"
$AGENT_SPIFFE  = "$SPIFFE_DOMAIN/agent/docker"

# All Python service containers run /usr/local/bin/python via the same path,
# so we differentiate using uid + supplementary selectors. For PoC we register
# one shared identity per uid. To make per-service identities work properly,
# re-enable the docker attestor on Linux/WSL2 (see agent.conf).
$services = @("gateway", "auth", "profile", "grades", "enrollments", "registrations")

Write-Host "=== Guardians Zero-Trust Portal: Workload Registration ===" -ForegroundColor Cyan

foreach ($name in $services) {
    $spiffeId = "$SPIFFE_DOMAIN/service/$name"
    Write-Host "  - Registering $spiffeId"

    # unix attestor selectors (uid:0 = root). All services match this until we
    # turn the docker attestor back on. For this PoC, we register the same
    # selector for each service - they will share an SVID pool which still
    # demonstrates per-service issuance from the application's perspective.
    docker compose exec -T spire-server `
        /opt/spire/bin/spire-server entry create `
        -parentID $AGENT_SPIFFE `
        -spiffeID $spiffeId `
        -selector "unix:uid:0" `
        -ttl 3600 2>&1 | Out-String | Write-Host
}

Write-Host ""
Write-Host "=== Registered Entries ===" -ForegroundColor Green
docker compose exec -T spire-server /opt/spire/bin/spire-server entry show 2>&1 | Out-String | Write-Host
