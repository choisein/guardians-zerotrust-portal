"""
shared/spire_client.py - SPIRE Workload API 클라이언트
──────────────────────────────────────────────────────
각 마이크로서비스는 SPIRE Agent 의 Workload API (Unix Socket) 를 통해
자신의 X.509-SVID / JWT-SVID 를 발급받습니다.

SVID 는 짧은 수명(기본 1시간)을 가지며 주기적으로 자동 갱신됩니다.

이 모듈은 PyPI 패키지 ``spiffe`` (구 ``pyspiffe``) 0.2.x 를 감싸서 단순한
인터페이스를 노출합니다. ``spiffe`` 가 설치되지 않은 환경(로컬 IDE 등)
에서도 import 만으로 죽지 않도록 graceful fallback 을 두었습니다.

주요 메서드:
  - ``fetch_jwt_svid(audience)``        : 호출 대상 서비스용 JWT-SVID 발급
  - ``validate_jwt_svid(token, aud)``   : 수신한 JWT-SVID 검증
  - ``close()``                         : 백그라운드 스트림 정리

환경변수:
  - ``SPIFFE_ENDPOINT_SOCKET``     : Workload API Unix Socket
                                    (예: unix:///run/spire/agent/public/api.sock)
  - ``SPIRE_AGENT_SOCKET``         : 위와 동일. 둘 중 아무거나 설정해도 됨.
                                    SPIFFE_ENDPOINT_SOCKET 이 우선.
  - ``SERVICE_SPIFFE_ID``          : 이 프로세스가 가지는 SPIFFE ID
                                    (예: spiffe://guardians.local/service/profile)
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# spiffe 패키지 import (graceful fallback)
# ──────────────────────────────────────────────────────────────────
try:
    from spiffe import JwtSource, JwtSvid, SpiffeId, TrustDomain  # type: ignore
    SPIFFE_AVAILABLE = True
except ImportError:  # 로컬에서 설치 안 됐을 때
    SPIFFE_AVAILABLE = False
    JwtSource = None  # type: ignore
    JwtSvid = None  # type: ignore
    SpiffeId = None  # type: ignore
    TrustDomain = None  # type: ignore
    logger.warning(
        "spiffe 라이브러리가 설치되어 있지 않습니다. "
        "DEV-SVID 더미 토큰 모드로 동작합니다."
    )


# ──────────────────────────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────────────────────────
def _resolve_socket_path() -> str:
    """SPIFFE_ENDPOINT_SOCKET 환경변수를 우선 사용하고,
    없으면 호환용 SPIRE_AGENT_SOCKET, 그것도 없으면 기본값을 반환."""
    return (
        os.environ.get("SPIFFE_ENDPOINT_SOCKET")
        or os.environ.get("SPIRE_AGENT_SOCKET")
        or "unix:///run/spire/agent/public/api.sock"
    )


# ──────────────────────────────────────────────────────────────────
# 클라이언트 본체
# ──────────────────────────────────────────────────────────────────
class SpireClient:
    """프로세스당 1 개만 만들어 재사용한다.

    내부적으로 ``JwtSource`` 가 백그라운드 gRPC 스트림을 유지하면서
    JWT 번들을 자동으로 갱신한다. 첫 번째 업데이트가 도착할 때까지는
    ``JwtSource`` 생성자가 블로킹되므로 ``timeout_in_seconds`` 를 지정해
    Agent 가 아직 안 떠있을 때 무한 대기하지 않도록 한다.
    """

    DEFAULT_INIT_TIMEOUT = float(os.environ.get("SPIFFE_INIT_TIMEOUT", "10"))

    def __init__(self, socket_path: str, service_spiffe_id: str):
        self.socket_path = socket_path
        self.service_spiffe_id = service_spiffe_id
        self._jwt_source: Optional["JwtSource"] = None
        self._lock = threading.Lock()

    # ──────────────────────────────────────
    # 내부: JwtSource 지연 초기화
    # ──────────────────────────────────────
    def _ensure_source(self) -> Optional["JwtSource"]:
        if not SPIFFE_AVAILABLE:
            return None
        if self._jwt_source is not None:
            return self._jwt_source
        with self._lock:
            if self._jwt_source is not None:
                return self._jwt_source
            # spiffe 라이브러리는 SPIFFE_ENDPOINT_SOCKET 를 보거나
            # 생성자 인자로 받은 socket_path 를 본다. 둘 다 세팅해 둔다.
            os.environ["SPIFFE_ENDPOINT_SOCKET"] = self.socket_path
            try:
                self._jwt_source = JwtSource(
                    socket_path=self.socket_path,
                    timeout_in_seconds=self.DEFAULT_INIT_TIMEOUT,
                )
                logger.info(
                    "JwtSource 초기화 완료 (socket=%s, spiffe_id=%s)",
                    self.socket_path,
                    self.service_spiffe_id,
                )
            except Exception as e:
                logger.error("JwtSource 초기화 실패: %s", e)
                self._jwt_source = None
            return self._jwt_source

    # ──────────────────────────────────────
    # JWT-SVID 발급 (호출자 → 상대 서비스)
    # ──────────────────────────────────────
    def fetch_jwt_svid(self, audience: str) -> Optional[str]:
        """호출 대상 서비스의 SPIFFE ID 를 audience 로 갖는 JWT-SVID 토큰을 반환.

        ``spiffe`` 미설치 환경에서는 ``DEV-SVID-<from>-><aud>`` 더미 토큰을
        반환해 미들웨어/OPA 흐름 테스트에는 지장 없도록 한다.
        """
        if not SPIFFE_AVAILABLE:
            logger.warning("spiffe 미설치 - DEV 더미 토큰 발급")
            return f"DEV-SVID-{self.service_spiffe_id}->{audience}"

        source = self._ensure_source()
        if source is None:
            return None

        try:
            svid = source.fetch_svid(audience={audience})
            return svid.token
        except Exception as e:
            logger.error("JWT-SVID 발급 실패 (audience=%s): %s", audience, e)
            return None

    # ──────────────────────────────────────
    # JWT-SVID 검증 (수신자 측)
    # ──────────────────────────────────────
    def validate_jwt_svid(self, token: str, expected_audience: str) -> Optional[dict]:
        """수신한 JWT-SVID 를 검증하고 호출자 SPIFFE ID 를 반환."""
        if not token:
            return None

        # 개발 모드: spiffe 미설치 시 더미 토큰 파싱
        if not SPIFFE_AVAILABLE:
            if token.startswith("DEV-SVID-"):
                try:
                    _, rest = token.split("DEV-SVID-", 1)
                    caller_id, _ = rest.split("->", 1)
                    return {"spiffe_id": caller_id, "expiry": None}
                except ValueError:
                    return None
            return None

        source = self._ensure_source()
        if source is None:
            return None

        try:
            # 1) 헤더에서 SPIFFE ID 를 미리 꺼내서 trust domain 파악
            insecure = JwtSvid.parse_insecure(token, audience={expected_audience})
            trust_domain: TrustDomain = insecure.spiffe_id.trust_domain
            jwt_bundle = source.get_bundle_for_trust_domain(trust_domain)
            if jwt_bundle is None:
                logger.warning(
                    "검증 실패: trust_domain %s 에 대한 JWT 번들 없음",
                    trust_domain,
                )
                return None

            # 2) 실제 서명/만료/audience 검증
            svid = JwtSvid.parse_and_validate(
                token=token,
                jwt_bundle=jwt_bundle,
                audience={expected_audience},
            )
            return {
                "spiffe_id": str(svid.spiffe_id),
                "expiry": svid.expiry,
                "audience": list(svid.audience),
            }
        except Exception as e:
            logger.warning("JWT-SVID 검증 실패: %s", e)
            return None

    # ──────────────────────────────────────
    # 정리
    # ──────────────────────────────────────
    def close(self) -> None:
        if self._jwt_source is not None:
            try:
                self._jwt_source.close()
            except Exception:
                pass
            self._jwt_source = None


# ──────────────────────────────────────────────────────────────────
# 프로세스 전역 싱글턴
# ──────────────────────────────────────────────────────────────────
_client: Optional[SpireClient] = None
_client_lock = threading.Lock()


def get_spire_client() -> SpireClient:
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            _client = SpireClient(
                socket_path=_resolve_socket_path(),
                service_spiffe_id=os.environ.get("SERVICE_SPIFFE_ID", ""),
            )
        return _client
