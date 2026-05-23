"""
shared/service_client.py - 서비스 간 직접 호출 클라이언트
─────────────────────────────────────────────────────────
한 마이크로서비스가 게이트웨이를 거치지 않고 다른 마이크로서비스를
직접 호출할 때 사용한다.

게이트웨이 경유 호출과의 결정적 차이:
  - 게이트웨이 호출: 게이트웨이가 자기 SVID 를 발급 → 수신측 source="gateway"
  - 서비스 간 호출: 호출 주체(자기 자신)가 자기 SVID 를 발급
                    → 수신측 source="service", caller_service=<나>

따라서 수신 서비스의 OPA 정책이 호출 그래프를 적용한다:
  - 허용된 엣지(enrollments→grades, enrollments→profile,
    registrations→enrollments)는 allow
  - 그래프 이탈(profile→grades 등)은 critical_violation
    → 호출한 서비스의 SVID 가 즉시 폐지된다 (횡적 이동 차단)
"""

import logging

import requests

from .spire_client import get_spire_client

logger = logging.getLogger(__name__)

# 서비스 이름 → (내부 URL, SPIFFE ID)
SERVICE_REGISTRY = {
    "auth": ("http://auth-service:5001", "spiffe://guardians.local/service/auth"),
    "profile": ("http://profile-service:5002", "spiffe://guardians.local/service/profile"),
    "grades": ("http://grades-service:5003", "spiffe://guardians.local/service/grades"),
    "enrollments": ("http://enrollments-service:5004", "spiffe://guardians.local/service/enrollments"),
    "registrations": ("http://registrations-service:5005", "spiffe://guardians.local/service/registrations"),
}


def call_service(target, path, method="GET", cookies=None, params=None, data=None, timeout=10):
    """다른 서비스를 직접 호출한다 (호출 주체 자신의 SVID 첨부).

    Args:
        target:  대상 서비스 이름 (SERVICE_REGISTRY 키, 예 "grades")
        path:    대상 경로 (예 "/api/student/grades")
        method:  HTTP 메서드
        cookies: 전달할 세션 쿠키 (최종 사용자 식별용)
        params:  쿼리 파라미터
        data:    요청 바디

    Returns:
        requests.Response (연결 실패 시 None)
    """
    if target not in SERVICE_REGISTRY:
        logger.error("알 수 없는 대상 서비스: %s", target)
        return None
    base_url, target_spiffe = SERVICE_REGISTRY[target]

    # 호출 주체(나 자신)의 JWT-SVID 발급 — audience 는 대상 서비스
    spire = get_spire_client()
    svid = spire.fetch_jwt_svid(audience=target_spiffe)

    headers = {}
    if svid:
        headers["X-SVID"] = svid

    try:
        return requests.request(
            method=method,
            url=f"{base_url}{path}",
            headers=headers,
            cookies=cookies,
            params=params,
            data=data,
            timeout=timeout,
        )
    except requests.RequestException as e:
        logger.error("서비스 호출 실패 (%s%s): %s", base_url, path, e)
        return None


def response_summary(resp):
    """데모 응답용: 다운스트림 응답을 status + body 로 요약한다."""
    if resp is None:
        return {"ok": False, "error": "연결 실패(연결 오류 또는 SVID 발급 불가)"}
    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text[:300]}
    return {"status": resp.status_code, "body": body}
