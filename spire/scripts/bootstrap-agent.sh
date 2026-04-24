#!/bin/sh
#
# bootstrap-agent.sh - SPIRE Agent 부트스트랩
# ───────────────────────────────────────────
# Agent가 Server에 처음 연결할 때 필요한 join_token을 생성하고
# trust bundle을 가져옵니다.
#
# 사용법 (docker-compose 최초 1회 실행):
#   docker compose exec spire-server sh /spire/scripts/bootstrap-agent.sh
#

set -e

echo "=== SPIRE Agent 부트스트랩 ==="

# 1) Join Token 발급 (Agent attestation 용)
TOKEN=$(/opt/spire/bin/spire-server token generate -spiffeID spiffe://guardians.local/agent/docker | awk '{print $2}')
echo "Join Token: $TOKEN"
echo "$TOKEN" > /run/spire/server/data/join_token

# 2) Trust bundle 내보내기
/opt/spire/bin/spire-server bundle show > /run/spire/server/data/bundle.crt
echo "Trust bundle exported to /run/spire/server/data/bundle.crt"

echo ""
echo "다음 명령으로 Agent 컨테이너를 실행하세요:"
echo "  docker compose up -d spire-agent"
