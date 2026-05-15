"""
shared/middleware.py - 요청 인증/인가 미들웨어 (OPA 이상탐지 + critical 폐기)
──────────────────────────────────────────────────────────────────────
모든 마이크로서비스는 다음 순서로 요청을 검증합니다.

  1) SVID 검증 (SPIFFE)
     - 호출자(게이트웨이 등)가 보낸 JWT-SVID 를 Workload API 로 검증
     - spiffe://guardians.local/... 형태의 caller ID 를 추출
     - blocklist (즉시 무효화 목록) 도 함께 확인

  2) 세션 검증 (Flask session / 쿠키)
     - 최종 사용자가 로그인 상태인지 확인

  3) OPA 인가 질의 (allow + critical_violation 동시 평가)
     - critical_violation == true: SPIRE entry 즉시 삭제 + blocklist 등록
     - allow == false           : 일반 deny (entry 유지)

context 필드:
  - hour: 현재 시각(0~23) - 시간대 기반 이상탐지용
  - recent_request_count: 최근 10초간 동일 사용자 요청 수 - 대량조회 탐지용
  - timestamp: 현재 시각 ISO 문자열 (로깅/감사용)
  - client_ip: 요청자 IP (감사용)

단일 데코레이터 @zero_trust_required 로 묶어 각 라우트에 적용합니다.
"""

import functools
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime
from threading import Lock

from flask import request, session, jsonify, g

from .spire_client import get_spire_client, revoke_entry
from .opa_client import get_opa_client

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 사용자별 최근 요청 시각 기록 (이상행동 탐지용)
#   - 메모리 기반: 서비스 재시작 시 초기화됨
#   - 운영 환경에서는 Redis 등 외부 저장소로 교체 권장
# ─────────────────────────────────────────────────────────────
_request_log: dict = defaultdict(lambda: deque(maxlen=100))
_request_log_lock = Lock()
ANOMALY_WINDOW_SECONDS = 10  # 최근 N초 이내 요청을 카운트


def _record_and_count_recent(user_key: str) -> int:
    """현재 요청을 기록하고, 최근 ANOMALY_WINDOW_SECONDS 초간 요청 수를 반환."""
    now = time.time()
    cutoff = now - ANOMALY_WINDOW_SECONDS

    with _request_log_lock:
        dq = _request_log[user_key]
        dq.append(now)
        # 윈도우 밖의 오래된 기록 정리
        while dq and dq[0] < cutoff:
            dq.popleft()
        return len(dq)


def zero_trust_required(policy_package: str, require_session: bool = True):
    """
    제로트러스트 요청 보호 데코레이터.

    Args:
        policy_package: OPA 정책 패키지 이름 (예 "guardians/profile")
        require_session: Flask 세션 인증을 함께 요구할지 여부
                         (로그인 서비스는 세션이 아직 없으므로 False)
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            my_spiffe_id = os.environ.get("SERVICE_SPIFFE_ID", "")

            # 1) SVID 검증 (헤더 X-SVID 로 전달)
            #    spire_client.validate_jwt_svid 내부에서 blocklist 도 확인한다.
            svid_token = request.headers.get("X-SVID")
            caller_spiffe_id = None

            if svid_token:
                spire = get_spire_client()
                claims = spire.validate_jwt_svid(svid_token, my_spiffe_id)
                if not claims:
                    return jsonify({"error": "유효하지 않은 SVID"}), 401
                caller_spiffe_id = claims["spiffe_id"]
                g.caller_spiffe_id = caller_spiffe_id
            else:
                # 개발 모드: 게이트웨이 미통과 요청은 거부
                if os.environ.get("REQUIRE_SVID", "true").lower() == "true":
                    return jsonify({"error": "X-SVID 헤더가 필요합니다."}), 401
                caller_spiffe_id = "dev-local"

            # 2) 세션 검증
            user_id = session.get("user_id")
            user_role = session.get("role")
            if require_session and not user_id:
                return jsonify({"error": "로그인이 필요합니다."}), 401

            # 3) 이상행동 탐지용 context 수집
            user_key = user_id or request.remote_addr or "anonymous"
            recent_count = _record_and_count_recent(user_key)

            now = datetime.now()
            context = {
                "hour": now.hour,
                "timestamp": now.isoformat(),
                "client_ip": request.remote_addr,
                "recent_request_count": recent_count,
            }

            # 4) OPA 인가 질의 (allow + critical_violation 동시)
            opa_input = {
                "caller_spiffe_id": caller_spiffe_id,
                "service_spiffe_id": my_spiffe_id,
                "user": {"user_id": user_id, "role": user_role},
                "method": request.method,
                "path": request.path,
                "query": dict(request.args),
                "context": context,
            }
            opa = get_opa_client()
            decision = opa.evaluate(policy_package, opa_input)

            # 4-a) critical_violation: 단순 거부가 아니라 신원 신뢰 박탈
            #      → 호출자(caller_spiffe_id) 의 SPIRE entry 를 즉시 삭제
            #      → 동시에 blocklist 에 등록되어 기존 SVID 도 즉시 무효화
            if decision.get("critical_violation"):
                logger.error(
                    "[CRITICAL] 신뢰 박탈 사유 탐지 → entry 삭제 시도: "
                    "caller=%s policy=%s input=%s",
                    caller_spiffe_id, policy_package, opa_input,
                )
                revoke_entry(caller_spiffe_id)
                return jsonify({
                    "error": "critical_violation 으로 SVID 가 폐기되었습니다.",
                    "reason": "critical_violation",
                }), 403

            # 4-b) 일반 deny: 접근 통제만 (entry 유지)
            if not decision.get("allow"):
                logger.warning("OPA 거부: %s", opa_input)
                return jsonify({"error": "정책에 의해 거부됨"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
