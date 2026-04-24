"""
gateway / app.py - API 게이트웨이
─────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/gateway
역할:
  1) 프론트엔드에서 오는 HTTP 요청을 수신
  2) 요청 경로에 따라 5개 마이크로서비스 중 하나로 프록시
  3) 프록시할 때 자신의 JWT-SVID를 발급받아 X-SVID 헤더로 첨부
  4) 프론트엔드 정적 파일 서빙

라우팅 규칙:
  /api/auth/*               → auth-service:5001
  /api/student/profile       → profile-service:5002
  /api/student/grades*       → grades-service:5003
  /api/student/enrollments   → enrollments-service:5004
  /api/student/registrations → registrations-service:5005

포트: 5000
"""

import os
import sys
from flask import Flask, request, Response, send_from_directory, jsonify
from flask_cors import CORS
import requests

sys.path.insert(0, "/app")

from shared.spire_client import get_spire_client

# ─────────────────────────────────────────────
# 업스트림 서비스 매핑
# ─────────────────────────────────────────────
UPSTREAMS = {
    "auth": {
        "url": os.environ.get("AUTH_URL", "http://auth-service:5001"),
        "spiffe_id": "spiffe://guardians.local/service/auth",
    },
    "profile": {
        "url": os.environ.get("PROFILE_URL", "http://profile-service:5002"),
        "spiffe_id": "spiffe://guardians.local/service/profile",
    },
    "grades": {
        "url": os.environ.get("GRADES_URL", "http://grades-service:5003"),
        "spiffe_id": "spiffe://guardians.local/service/grades",
    },
    "enrollments": {
        "url": os.environ.get("ENROLLMENTS_URL", "http://enrollments-service:5004"),
        "spiffe_id": "spiffe://guardians.local/service/enrollments",
    },
    "registrations": {
        "url": os.environ.get("REGISTRATIONS_URL", "http://registrations-service:5005"),
        "spiffe_id": "spiffe://guardians.local/service/registrations",
    },
}


def route_service(path: str):
    """요청 경로를 분석해 어느 서비스로 보낼지 결정."""
    if path.startswith("/api/auth"):
        return "auth"
    if path.startswith("/api/student/profile"):
        return "profile"
    if path.startswith("/api/student/grades"):
        return "grades"
    if path.startswith("/api/student/enrollments"):
        return "enrollments"
    if path.startswith("/api/student/registrations"):
        return "registrations"
    return None


def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.environ.get("FRONTEND_DIR", "/app/frontend")

    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "guardians-gateway-secret")
    CORS(app, supports_credentials=True)

    # ─────────────────────────────────────────
    # 프록시 핸들러
    # ─────────────────────────────────────────
    @app.route("/api/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    def proxy(subpath):
        full_path = f"/api/{subpath}"
        svc = route_service(full_path)
        if svc is None:
            return jsonify({"error": f"라우팅 실패: {full_path}"}), 404

        upstream = UPSTREAMS[svc]
        target_url = f"{upstream['url']}{full_path}"

        # 이 요청을 처리할 서비스의 SPIFFE ID를 audience로 JWT-SVID 발급
        spire = get_spire_client()
        svid = spire.fetch_jwt_svid(audience=upstream["spiffe_id"])

        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
        if svid:
            headers["X-SVID"] = svid

        try:
            resp = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.args,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                timeout=10,
            )
        except requests.RequestException as e:
            return jsonify({"error": f"업스트림 연결 실패: {e}"}), 502

        excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        response_headers = [(k, v) for k, v in resp.raw.headers.items() if k.lower() not in excluded]
        return Response(resp.content, status=resp.status_code, headers=response_headers)

    # ─────────────────────────────────────────
    # 프론트엔드 정적 파일 서빙
    # ─────────────────────────────────────────
    @app.route("/")
    def index():
        return send_from_directory(os.path.join(frontend_dir, "templates"), "login.html")

    @app.route("/templates/<path:filename>")
    def serve_template(filename):
        return send_from_directory(os.path.join(frontend_dir, "templates"), filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(os.path.join(frontend_dir, "css"), filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(os.path.join(frontend_dir, "js"), filename)

    # 레거시 경로: 일부 HTML이 "../static/css/..." 식으로 참조함
    @app.route("/static/css/<path:filename>")
    def serve_css_static(filename):
        return send_from_directory(os.path.join(frontend_dir, "css"), filename)

    @app.route("/static/js/<path:filename>")
    def serve_js_static(filename):
        return send_from_directory(os.path.join(frontend_dir, "js"), filename)

    @app.route("/health")
    def health():
        return jsonify({
            "service": "gateway",
            "spiffe_id": os.environ.get("SERVICE_SPIFFE_ID"),
            "upstreams": list(UPSTREAMS.keys()),
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    print(f"🌐 Gateway (SPIFFE: {os.environ.get('SERVICE_SPIFFE_ID')}) on :5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
