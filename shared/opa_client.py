"""
shared/opa_client.py - OPA(Open Policy Agent) 클라이언트
────────────────────────────────────────────────────────
각 마이크로서비스는 요청을 처리하기 전에 OPA에 "이 요청을 허용해도 되는가?"
를 질의합니다. OPA는 Rego 정책을 기반으로 SPIFFE ID, 사용자 role, 경로 등을
확인하여 allow/deny 결정을 내립니다.

OPA는 HTTP API(Data API)를 통해 질의합니다.
  POST /v1/data/<package>/allow                 -- allow 만
  POST /v1/data/<package>                       -- allow + critical_violation 일괄
  body: {"input": {...}}

profile / grades / registrations 정책은 `allow` 외에 `critical_violation`
키도 노출한다. critical_violation == true 인 경우 미들웨어가 SPIRE entry 를
삭제해 SVID 를 즉시 폐기한다.
"""

import logging
import os
import requests
from typing import Any, Dict

logger = logging.getLogger(__name__)


class OpaClient:
    def __init__(self, opa_url: str, service_name: str):
        self.opa_url = opa_url.rstrip("/")
        self.service_name = service_name

    def check(self, policy_package: str, input_data: Dict[str, Any]) -> bool:
        """
        지정한 정책 패키지에 대해 allow 여부를 질의.

        Args:
            policy_package: 예 "guardians/profile"
            input_data: OPA input으로 전달할 딕셔너리
                        {"caller_spiffe_id": "...", "user": {...}, "method": "GET", ...}

        Returns:
            True이면 허용, False이면 거부.
        """
        url = f"{self.opa_url}/v1/data/{policy_package}/allow"
        try:
            resp = requests.post(url, json={"input": input_data}, timeout=3)
            if resp.status_code != 200:
                logger.warning(f"OPA 질의 실패 ({resp.status_code}): {resp.text}")
                return False
            result = resp.json().get("result", False)
            return bool(result)
        except requests.RequestException as e:
            logger.error(f"OPA 연결 실패: {e}")
            # 페일 클로즈: OPA에 도달할 수 없으면 거부
            return False

    def evaluate(self, policy_package: str, input_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        정책 패키지를 통째로 질의하여 ``allow`` 와 ``critical_violation`` 을
        한 번에 반환한다.

        Returns:
            {"allow": bool, "critical_violation": bool}
            - OPA 도달 불가 / 응답 오류 시 페일 클로즈: allow=False, critical_violation=False
              (critical 은 "확실히 탐지된 경우에만" True 로 두어 false-positive 폐기를
               방지한다.)
        """
        url = f"{self.opa_url}/v1/data/{policy_package}"
        try:
            resp = requests.post(url, json={"input": input_data}, timeout=3)
            if resp.status_code != 200:
                logger.warning(f"OPA 질의 실패 ({resp.status_code}): {resp.text}")
                return {"allow": False, "critical_violation": False}
            result = resp.json().get("result", {}) or {}
            return {
                "allow": bool(result.get("allow", False)),
                "critical_violation": bool(result.get("critical_violation", False)),
            }
        except requests.RequestException as e:
            logger.error(f"OPA 연결 실패: {e}")
            return {"allow": False, "critical_violation": False}


_opa: OpaClient = None


def get_opa_client() -> OpaClient:
    global _opa
    if _opa is None:
        _opa = OpaClient(
            os.environ.get("OPA_URL", "http://opa:8181"),
            os.environ.get("SERVICE_NAME", "unknown"),
        )
    return _opa
