# diag-svid.ps1 - SVID 발급 흐름 통합 진단
# -----------------------------------------
# 한 번에:
#   1) compose down -v 로 SPIRE 상태 초기화
#   2) server → bootstrap → agent → register → 모든 서비스 기동
#   3) gateway 안에서 SVID 발급 시도
#   4) agent 의 디버그 로그 출력
#
# 한 번 실행하고 마지막에 출력되는 로그를 그대로 복사해 보내면 된다.
$ErrorActionPreference = "Continue"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Section($t) {
    Write-Host ""
    Write-Host "=== $t ===" -ForegroundColor Cyan
}

# ─── 1) 깨끗하게 내림 ───────────────────────────────
Section "1) compose down -v (전체 초기화)"
docker compose down -v --remove-orphans 2>&1 | Out-String | Write-Host

# ─── 2) Server 기동 ─────────────────────────────────
Section "2) spire-server 기동"
docker compose up -d spire-server 2>&1 | Out-String | Write-Host
Start-Sleep -Seconds 4

# ─── 3) Bootstrap (join token 발급) ────────────────
Section "3) bootstrap-agent.ps1 (join token)"
powershell -ExecutionPolicy Bypass -File .\spire\scripts\bootstrap-agent.ps1 2>&1 | Out-String | Write-Host

# ─── 4) Agent 기동 ─────────────────────────────────
Section "4) spire-agent 기동"
docker compose up -d spire-agent 2>&1 | Out-String | Write-Host
Start-Sleep -Seconds 6

Section "4-a) agent 상태"
docker compose ps spire-agent 2>&1 | Out-String | Write-Host

# ─── 5) Workload entry 등록 ────────────────────────
Section "5) register-workloads.ps1 (docker:label selector)"
powershell -ExecutionPolicy Bypass -File .\spire\scripts\register-workloads.ps1 2>&1 | Out-String | Write-Host

# ─── 6) 나머지 서비스 기동 ─────────────────────────
Section "6) 모든 서비스 기동"
docker compose up -d 2>&1 | Out-String | Write-Host
Start-Sleep -Seconds 5

Section "6-a) 전체 컨테이너 상태"
docker compose ps 2>&1 | Out-String | Write-Host

# ─── 7) Gateway 안에서 호스트 정보 확인 ────────────
Section "7) gateway 컨테이너 안에서 자기 PID/cgroup 확인"
docker compose exec -T gateway sh -c "echo '--- /proc/self/cgroup ---'; cat /proc/self/cgroup; echo '--- 자기 PID ---'; echo \$\$" 2>&1 | Out-String | Write-Host

# ─── 8) Agent 안에서 docker.sock / proc 접근성 확인 ─
Section "8) agent 컨테이너 안에서 docker.sock + 호스트 PID 확인"
docker compose exec -T spire-agent /bin/sh -c "ls -la /var/run/docker.sock 2>&1; echo '--- /proc 의 PID 일부 ---'; ls /proc 2>&1 | head -20" 2>&1 | Out-String | Write-Host

# ─── 9) gateway 가 SVID 발급 시도 ─────────────────
Section "9) gateway 에서 fetch_jwt_svid 시도"
docker compose exec -T gateway python -c "
import logging; logging.basicConfig(level=logging.DEBUG)
from shared.spire_client import get_spire_client
print('==> fetch result:', get_spire_client().fetch_jwt_svid('spiffe://guardians.local/service/auth'))
" 2>&1 | Out-String | Write-Host

Start-Sleep -Seconds 2

# ─── 10) Agent DEBUG 로그 (가장 중요!) ─────────────
Section "10) spire-agent 최근 DEBUG 로그 (workload attestor 호출 흔적)"
docker compose logs --tail=120 spire-agent 2>&1 | Out-String | Write-Host

Section "DONE"
Write-Host "위 출력 전체를 복사해 보내주세요."
