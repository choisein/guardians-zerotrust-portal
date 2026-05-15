"""
shared/spire_client.py - SPIRE Workload API 클라이언트
──────────────────────────────────────────────────────
각 마이크로서비스는 SPIRE Agent 의 Workload API (Unix Socket) 를 통해
자신의 X.509-SVID / JWT-SVID 를 발급받습니다.

SVID 는 짧은 수명(기본 1시간)을 가지며 주기적으로 자동 갱신됩니다.

주요 메서드:
  - ``fetch_jwt_svid(audience)``        : 호출 대상 서비스용 JWT-SVID 발급
  - ``validate_jwt_svid(token, aud)``   : 수신한 JWT-SVID 검증 (+blocklist 차단)
  - ``revoke_entry(spiffe_id)``         : SPIRE entry 삭제 + blocklist 등록
  - ``is_revoked(spiffe_id)``           : 즉시 무효화 여부 확인
  - ``close()``                         : 백그라운드 스트림 정리

[즉시 무효화]
  SPIRE entry 를 삭제해도 이미 발급된 JWT/X.509-SVID 는 만료까지 유효하다.
  ``revoke_entry`` 는 entry 삭제와 동시에 SPIFFE ID 를 in-memory blocklist
  에 추가하고, ``validate_jwt_svid`` 는 검증 시 blocklist 를 먼저 본다.
  이렇게 함으로써 'entry 삭제 = SVID 즉시 무효화' 가 수신자 측에서 강제된다.
  (멀티 호스트로 확장할 경우 Redis 등 외부 저장소로 교체할 것)

환경변수:
  - SPIFFE_ENDPOINT_SOCKET   : Workload API Unix Socket
  - SPIRE_AGENT_SOCKET       : 위와 동일 (호환용)
  - SERVICE_SPIFFE_ID        : 이 프로세스가 가지는 SPIFFE ID
  - SPIRE_SERVER_CONTAINER   : SPIRE Server 컨테이너 이름 (entry 삭제 시 사용)
  - SPIRE_SERVER_BIN         : SPIRE Server CLI 경로
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# spiffe 패키지 import (graceful fallback)
# ──────────────────────────────────────────────────────────────────
try:
    from spiffe import JwtSource, JwtSvid, SpiffeId, TrustDomain  # type: ignore
    SPIFFE_AVAILABLE = True
except ImportError:
    SPIFFE_AVAILABLE = False
    JwtSource = None  # type: ignore
    JwtSvid = None  # type: ignore
    SpiffeId = None  # type: ignore
    TrustDomain = None  # type: ignore
    logger.warning(
        "spiffe 라이브러리가 설치되어 있지 않습니다. "
        "DEV-SVID 더미 토큰 모드로 동작합니다."
    )


def _resolve_socket_path() -> str:
    return (
        os.environ.get("SPIFFE_ENDPOINT_SOCKET")
        or os.environ.get("SPIRE_AGENT_SOCKET")
        or "unix:///run/spire/agent/public/api.sock"
    )


# ──────────────────────────────────────────────────────────────────
# SPIFFE ID Blocklist (즉시 무효화)
# ──────────────────────────────────────────────────────────────────
# entry 가 삭제되어도 기존에 발급된 SVID 는 만료까지 유효하기 때문에,
# 수신 측에서 검증 시 차단 목록을 한 번 더 확인해 즉시 무효화를 보장한다.
_revoked_spiffe_ids: set[str] = set()
_revoked_lock = threading.Lock()


def add_to_blocklist(spiffe_id: str) -> None:
    """SPIFFE ID 를 즉시 무효화 목록에 등록한다."""
    if not spiffe_id:
        return
    with _revoked_lock:
        _revoked_spiffe_ids.add(spiffe_id)
    logger.warning("[BLOCKLIST] SPIFFE ID 차단 등록: %s", spiffe_id)


def is_revoked(spiffe_id: str) -> bool:
    """SPIFFE ID 가 차단 목록에 있는지 확인한다."""
    if not spiffe_id:
        return False
    with _revoked_lock:
        return spiffe_id in _revoked_spiffe_ids


def clear_blocklist() -> None:
    """테스트/디버깅용: 차단 목록 초기화."""
    with _revoked_lock:
        _revoked_spiffe_ids.clear()


# ──────────────────────────────────────────────────────────────────
# 클라이언트 본체
# ──────────────────────────────────────────────────────────────────
class SpireClient:
    DEFAULT_INIT_TIMEOUT = float(os.environ.get("SPIFFE_INIT_TIMEOUT", "10"))

    def __init__(self, socket_path: str, service_spiffe_id: str):
        self.socket_path = socket_path
        self.service_spiffe_id = service_spiffe_id
        self._jwt_source: Optional["JwtSource"] = None
        self._lock = threading.Lock()

    def _ensure_source(self) -> Optional["JwtSource"]:
        if not SPIFFE_AVAILABLE:
            return None
        if self._jwt_source is not None:
            return self._jwt_source
        with self._lock:
            if self._jwt_source is not None:
                return self._jwt_source
            os.environ["SPIFFE_ENDPOINT_SOCKET"] = self.socket_path
            try:
                self._jwt_source = JwtSource(
                    socket_path=self.socket_path,
                    timeout_in_seconds=self.DEFAULT_INIT_TIMEOUT,
                )
                logger.info(
                    "JwtSource 초기화 완료 (socket=%s, spiffe_id=%s)",
                    self.socket_path, self.service_spiffe_id,
                )
            except Exception as e:
                logger.error("JwtSource 초기화 실패: %s", e)
                self._jwt_source = None
            return self._jwt_source

    def fetch_jwt_svid(self, audience: str) -> Optional[str]:
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

    def validate_jwt_svid(self, token: str, expected_audience: str) -> Optional[dict]:
        """수신한 JWT-SVID 를 검증하고 호출자 SPIFFE ID 를 반환.
        blocklist 에 있으면 서명·만료가 유효해도 즉시 거부한다."""
        if not token:
            return None

        # 개발 모드: spiffe 미설치 시 더미 토큰 파싱
        if not SPIFFE_AVAILABLE:
            if token.startswith("DEV-SVID-"):
                try:
                    _, rest = token.split("DEV-SVID-", 1)
                    caller_id, _ = rest.split("->", 1)
                    if is_revoked(caller_id):
                        logger.warning(
                            "[BLOCKLIST] 폐기된 SPIFFE ID 의 DEV-SVID 거부: %s",
                            caller_id,
                        )
                        return None
                    return {"spiffe_id": caller_id, "expiry": None}
                except ValueError:
                    return None
            return None

        source = self._ensure_source()
        if source is None:
            return None

        try:
            insecure = JwtSvid.parse_insecure(token, audience={expected_audience})
            trust_domain: TrustDomain = insecure.spiffe_id.trust_domain
            jwt_bundle = source.get_bundle_for_trust_domain(trust_domain)
            if jwt_bundle is None:
                logger.warning(
                    "검증 실패: trust_domain %s 에 대한 JWT 번들 없음",
                    trust_domain,
                )
                return None

            svid = JwtSvid.parse_and_validate(
                token=token,
                jwt_bundle=jwt_bundle,
                audience={expected_audience},
            )
            caller_id = str(svid.spiffe_id)
            # 서명·만료가 유효하더라도 blocklist 에 있으면 즉시 거부
            if is_revoked(caller_id):
                logger.warning(
                    "[BLOCKLIST] 폐기된 SPIFFE ID 의 JWT-SVID 거부: %s",
                    caller_id,
                )
                return None
            return {
                "spiffe_id": caller_id,
                "expiry": svid.expiry,
                "audience": list(svid.audience),
            }
        except Exception as e:
            logger.warning("JWT-SVID 검증 실패: %s", e)
            return None

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


# ──────────────────────────────────────────────────────────────────
# SPIRE Server admin: entry 삭제 (critical_violation 시 호출)
# ──────────────────────────────────────────────────────────────────
SPIRE_SERVER_CONTAINER = os.environ.get("SPIRE_SERVER_CONTAINER", "spire-server")
SPIRE_SERVER_BIN = os.environ.get("SPIRE_SERVER_BIN", "/opt/spire/bin/spire-server")


def _spire_server_exec(args: list[str]) -> Optional[str]:
    """docker exec spire-server /opt/spire/bin/spire-server ... 를 실행."""
    cmd = ["docker", "exec", SPIRE_SERVER_CONTAINER, SPIRE_SERVER_BIN] + args
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=5
        )
        return out.stdout
    except FileNotFoundError:
        logger.error("docker CLI 가 없어 SPIRE entry 명령을 실행할 수 없습니다.")
        return None
    except subprocess.CalledProcessError as e:
        logger.error("spire-server 호출 실패: %s", e.stderr.strip())
        return None
    except subprocess.TimeoutExpired:
        logger.error("spire-server 호출 타임아웃")
        return None


def find_entry_id(spiffe_id: str) -> Optional[str]:
    """SPIFFE ID 로 등록된 SPIRE entry 의 Entry ID 를 찾는다."""
    out = _spire_server_exec(["entry", "show", "-spiffeID", spiffe_id])
    if not out:
        return None
    for line in out.splitlines():
        if line.strip().startswith("Entry ID"):
            return line.split(":", 1)[1].strip()
    return None


def revoke_entry(spiffe_id: str) -> bool:
    """SPIFFE ID 의 SPIRE entry 를 삭제하고 즉시 차단 목록에 등록한다.

    1) blocklist 등록 → 이미 발급되어 살아 있는 기존 SVID 도 수신자 측
                       검증에서 즉시 거부됨 ("즉시 무효화")
    2) entry 삭제   → 이후 신규 SVID 발급은 SPIRE 측에서 자동 차단됨

    Returns:
        True  : entry 삭제 + blocklist 등록 성공
        False : entry 가 없거나 삭제 실패 (이 경우에도 blocklist 에는 등록됨)
    """
    if not spiffe_id:
        return False
    # 어떤 경우든 즉시 무효화 효과는 보장하기 위해 blocklist 부터 등록
    add_to_blocklist(spiffe_id)
    entry_id = find_entry_id(spiffe_id)
    if not entry_id:
        logger.warning("[REVOKE] entry 없음 (이미 폐기됨?): %s", spiffe_id)
        return False
    out = _spire_server_exec(["entry", "delete", "-entryID", entry_id])
    if out is None:
        return False
    logger.warning(
        "[REVOKE] SVID 폐기 완료: %s (entry=%s, blocklist 등록됨)",
        spiffe_id, entry_id,
    )
    return True
