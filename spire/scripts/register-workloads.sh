#!/bin/sh
#
# register-workloads.sh - 서비스별 SPIFFE ID 등록 스크립트
# ────────────────────────────────────────────────────────
# docker-compose 실행 후 SPIRE Server 컨테이너 안에서 1회 실행합니다.
#
#   docker compose exec spire-server sh /spire/scripts/register-workloads.sh
#
# 각 서비스는 docker 라벨(com.guardians.service=<name>)을 기반으로 attestation됩니다.
#

set -e

SPIFFE_DOMAIN="spiffe://guardians.local"
AGENT_SPIFFE="${SPIFFE_DOMAIN}/agent/docker"

echo "=== Guardians Zero-Trust Portal: Workload 등록 시작 ==="

# ─────────────────────────────────────────────
# 각 서비스별 등록
#   -parentID : Agent의 SPIFFE ID (모든 워크로드의 부모)
#   -spiffeID : 서비스의 고유 SPIFFE ID
#   -selector : docker 라벨 기반 식별
# ─────────────────────────────────────────────

register() {
    local name=$1
    echo "  - Registering ${SPIFFE_DOMAIN}/service/${name}"
    /opt/spire/bin/spire-server entry create \
        -parentID "${AGENT_SPIFFE}" \
        -spiffeID "${SPIFFE_DOMAIN}/service/${name}" \
        -selector "docker:label:com.guardians.service:${name}" \
        -ttl 3600 || true
}

# 1. Gateway
register "gateway"

# 2. Auth (로그인)
register "auth"

# 3. Profile (학적조회)
register "profile"

# 4. Grades (성적조회)
register "grades"

# 5. Enrollments (수강내역조회)
register "enrollments"

# 6. Registrations (등록금납부조회)
register "registrations"

echo ""
echo "=== 등록 완료 ==="
/opt/spire/bin/spire-server entry show
