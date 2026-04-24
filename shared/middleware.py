"""
shared/middleware.py - 요청 인증/인가 미들웨어
──────────────────────────────────────────────
모든 마이크로서비스는 다음 순서로 요청을 검증합니다.

  1) SVID 검증 (SPIFFE)
     - 호출자(게이트웨이 등)가 보낸 JWT-SVID를 Workload API로 검증
     - spiffe://guardians.local/... 형태의 caller ID를 추출

  2) 세션 검증 (Flask session / 쿠키)
     - 최종 사용자가 로그인 상태인지 확인

  3) OPA 인가 질의
     - caller_spiffe_id, user role, method, path 등을 input으로 질의
     - 거부되면 403 반환

단일 데코레이터 @zero_trust_required 로 묶어 각 라우트에 적용합니다.
"""

import functools
import logging
from flask import request, session, jsonify, g

from .spire_client import get_spire_client
from .opa_client import get_opa_client

logger = logging.getLogger(__name__)


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
            import os

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

            # 3) OPA 인가 질의
            opa_input = {
                "caller_spiffe_id": caller_spiffe_id,
                "service_spiffe_id": my_spiffe_id,
                "user": {"user_id": user_id, "role": user_role},
                "method": request.method,
                "path": request.path,
                "query": dict(request.args),
            }
            opa = get_opa_client()
            if not opa.check(policy_package, opa_input):
                logger.warning(f"OPA 거부: {opa_input}")
                return jsonify({"error": "정책에 의해 거부됨"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
