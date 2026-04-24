"""
shared/spire_client.py - SPIRE Workload API 클라이언트
──────────────────────────────────────────────────────
각 마이크로서비스는 SPIRE Agent의 Workload API(Unix Socket)를 통해
자신의 X.509-SVID 또는 JWT-SVID를 발급받습니다.

SVID는 짧은 수명(기본 1시간)을 가지며, 주기적으로 자동 갱신됩니다.

이 모듈은 pyspiffe 라이브러리를 감싸서 간단한 인터페이스를 제공합니다.
pyspiffe가 설치되지 않은 환경(로컬 개발)에서도 동작하도록 graceful fallback을 지원합니다.

주요 기능:
  - fetch_jwt_svid(audience): JWT-SVID 발급 (서비스 간 인증)
  - validate_jwt_svid(token, audience): 수신한 JWT-SVID 검증
  - get_x509_context(): X.509-SVID 및 신뢰 번들 조회
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from pyspiffe.workloadapi.default_jwt_source import DefaultJwtSource
    from pyspiffe.workloadapi.default_x509_source import DefaultX509Source
    from pyspiffe.spiffe_id.spiffe_id import SpiffeId
    from pyspiffe.svid.jwt_svid import JwtSvid
    PYSPIFFE_AVAILABLE = True
except ImportError:
    PYSPIFFE_AVAILABLE = False
    logger.warning("pyspiffe 라이브러리가 없습니다. SVID 검증이 비활성화됩니다.")


class SpireClient:
    """
    서비스별 SPIRE Agent 연동 클라이언트.

    각 서비스 프로세스 시작 시 한 번 인스턴스화하여 사용합니다.
    내부적으로 SPIRE Agent Workload API에 연결된 상태를 유지합니다.
    """

    def __init__(self, socket_path: str, service_spiffe_id: str):
        self.socket_path = socket_path
        self.service_spiffe_id = service_spiffe_id
        self._jwt_source: Optional["DefaultJwtSource"] = None
        self._x509_source: Optional["DefaultX509Source"] = None

    def _ensure_sources(self):
        """JWT/X509 소스를 지연 초기화."""
        if not PYSPIFFE_AVAILABLE:
            return
        if self._jwt_source is None:
            os.environ["SPIFFE_ENDPOINT_SOCKET"] = self.socket_path
            self._jwt_source = DefaultJwtSource(
                workload_api_client=None, timeout_in_seconds=10
            )
        if self._x509_source is None:
            self._x509_source = DefaultX509Source(
                workload_api_client=None, timeout_in_seconds=10
            )

    def fetch_jwt_svid(self, audience: str) -> Optional[str]:
        """
        지정한 audience에 대한 JWT-SVID를 발급받아 문자열로 반환합니다.

        Args:
            audience: 호출 대상 서비스의 SPIFFE ID
                      (예: spiffe://guardians.local/service/profile)

        Returns:
            JWT 토큰 문자열 (없으면 None)
        """
        if not PYSPIFFE_AVAILABLE:
            logger.warning("pyspiffe 미설치 - 더미 토큰 반환")
            return f"DEV-SVID-{self.service_spiffe_id}->{audience}"

        try:
            self._ensure_sources()
            svid: JwtSvid = self._jwt_source.get_jwt_svid(audiences=[audience])
            return svid.token
        except Exception as e:
            logger.error(f"JWT-SVID 발급 실패: {e}")
            return None

    def validate_jwt_svid(self, token: str, expected_audience: str) -> Optional[dict]:
        """
        수신한 JWT-SVID를 검증합니다.

        Args:
            token: 상대방이 보낸 JWT-SVID
            expected_audience: 이 서비스의 SPIFFE ID

        Returns:
            검증 성공 시 {"spiffe_id": "...", "expiry": ...}
            실패 시 None
        """
        if not PYSPIFFE_AVAILABLE:
            # 개발 모드: 더미 토큰 파싱
            if token and token.startswith("DEV-SVID-"):
                try:
                    _, rest = token.split("DEV-SVID-", 1)
                    caller_id, _ = rest.split("->", 1)
                    return {"spiffe_id": caller_id, "expiry": None}
                except ValueError:
                    return None
            return None

        try:
            self._ensure_sources()
            svid = JwtSvid.parse_and_validate(
                token=token,
                jwt_bundle_source=self._jwt_source,
                audiences=[expected_audience],
            )
            return {
                "spiffe_id": str(svid.spiffe_id),
                "expiry": svid.expiry,
            }
        except Exception as e:
            logger.error(f"JWT-SVID 검증 실패: {e}")
            return None

    def close(self):
        if self._jwt_source:
            try:
                self._jwt_source.close()
            except Exception:
                pass
        if self._x509_source:
            try:
                self._x509_source.close()
            except Exception:
                pass


# 싱글턴 인스턴스
_client: Optional[SpireClient] = None


def get_spire_client() -> SpireClient:
    """현재 프로세스 전역에서 쓰이는 SpireClient를 반환."""
    global _client
    if _client is None:
        socket = os.environ.get(
            "SPIRE_AGENT_SOCKET", "unix:///tmp/spire-agent/public/api.sock"
        )
        spiffe_id = os.environ.get("SERVICE_SPIFFE_ID", "")
        _client = SpireClient(socket, spiffe_id)
    return _client
