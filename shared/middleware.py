"""
shared/middleware.py - 요청 인증/인가 미들웨어 (OPA 이상탐지 확장판)
──────────────────────────────────────────────────────────────────────
모든 마이크로서비스는 다음 순서로 요청을 검증합니다.

  1) SVID 검증 (SPIFFE)
     - 호출자(게이트웨이 등)가 보낸 JWT-SVID를 Workload API로 검증
     - spiffe://guardians.local/... 형태의 caller ID를 추출

  2) 세션 검증 (Flask session / 쿠키)
     - 최종 사용자가 로그인 상태인지 확인

  3) OPA 인가 질의
     - caller_spiffe_id, user role, method, path, context를 input으로 질의
     - 거부되면 403 반환

[추가] context 필드:
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

from .spire_client import get_spire_client
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
            #    - 사용자가 있으면 user_id 기준, 없으면 IP 기준으로 카운트
            user_key = user_id or request.remote_addr or "anonymous"
            recent_count = _record_and_count_recent(user_key)

            now = datetime.now()
            context = {
                "hour": now.hour,
                "timestamp": now.isoformat(),
                "client_ip": request.remote_addr,
                "recent_request_count": recent_count,
            }

            # 4) OPA 인가 질의
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
            if not opa.check(policy_package, opa_input):
                logger.warning(f"OPA 거부: {opa_input}")
                return jsonify({"error": "정책에 의해 거부됨"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
