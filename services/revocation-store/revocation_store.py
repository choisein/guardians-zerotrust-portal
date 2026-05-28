"""
revocation-store - 폐지된 서비스 신원 저장소
─────────────────────────────────────────────
critical_violation 으로 SVID 가 폐지된 서비스를 기록한다.
미들웨어가 폐지 시 POST /revoke 로 알려주고, 게이트웨이는 공유 볼륨의
<service>.revoked 파일을 보고 해당 서비스를 replica 로 우회한다.

저장 위치: REVOCATION_DIR (기본 /revoked, 게이트웨이와 공유 볼륨)
"""

import os

from flask import Flask, request, jsonify

app = Flask(__name__)

REVOCATION_DIR = os.environ.get("REVOCATION_DIR", "/revoked")
os.makedirs(REVOCATION_DIR, exist_ok=True)
SUFFIX = ".revoked"


def _service_name(spiffe_id: str) -> str:
    """spiffe://guardians.local/service/profile → "profile" """
    return spiffe_id.rstrip("/").split("/")[-1]


@app.route("/revoke", methods=["POST"])
def revoke():
    data = request.get_json(silent=True) or {}
    spiffe_id = data.get("spiffe_id", "")
    if not spiffe_id:
        return jsonify({"error": "spiffe_id required"}), 400

    service_name = _service_name(spiffe_id)
    path = os.path.join(REVOCATION_DIR, f"{service_name}{SUFFIX}")
    with open(path, "w") as f:
        f.write(spiffe_id)

    print(f"[REVOCATION] {service_name} revoked ({spiffe_id})", flush=True)
    return jsonify({"status": "revoked", "service": service_name})


@app.route("/revoked", methods=["GET"])
def list_revoked():
    names = [
        f[: -len(SUFFIX)]
        for f in os.listdir(REVOCATION_DIR)
        if f.endswith(SUFFIX)
    ]
    return jsonify({"revoked": names})


@app.route("/reset", methods=["POST"])
def reset():
    """데모 반복용: 모든 폐지 기록 삭제."""
    cleared = []
    for f in os.listdir(REVOCATION_DIR):
        if f.endswith(SUFFIX):
            os.remove(os.path.join(REVOCATION_DIR, f))
            cleared.append(f[: -len(SUFFIX)])
    print(f"[REVOCATION] reset: {cleared}", flush=True)
    return jsonify({"status": "reset", "cleared": cleared})


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
