"""
auth-service / app.py - 로그인 서비스
─────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/auth
역할: 로그인, 로그아웃, 세션 확인

엔드포인트:
  POST /api/auth/login
  POST /api/auth/logout
  GET  /api/auth/session

포트: 5001
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# shared 모듈 import (도커 빌드 시 /app/shared 로 복사됨)
sys.path.insert(0, "/app")

from shared.models import db
from shared.config import BaseConfig
from routes.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    db.init_app(app)
    CORS(app, supports_credentials=True)

    app.register_blueprint(auth_bp)

    @app.route("/health")
    def health():
        return jsonify({
            "service": "auth-service",
            "spiffe_id": os.environ.get("SERVICE_SPIFFE_ID"),
            "status": "ok",
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    print(f"🔐 Auth Service (SPIFFE: {os.environ.get('SERVICE_SPIFFE_ID')}) on :5001")
    app.run(host="0.0.0.0", port=5001, debug=True)
