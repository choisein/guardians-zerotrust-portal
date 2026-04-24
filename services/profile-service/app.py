"""
profile-service / app.py - 학적조회 서비스
──────────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/profile
역할: 학생 기본 정보(학적) 조회

엔드포인트:
  GET /api/student/profile

포트: 5002
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

sys.path.insert(0, "/app")

from shared.models import db
from shared.config import BaseConfig
from routes.profile import profile_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    db.init_app(app)
    CORS(app, supports_credentials=True)

    app.register_blueprint(profile_bp)

    @app.route("/health")
    def health():
        return jsonify({
            "service": "profile-service",
            "spiffe_id": os.environ.get("SERVICE_SPIFFE_ID"),
            "status": "ok",
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    print(f"📋 Profile Service (SPIFFE: {os.environ.get('SERVICE_SPIFFE_ID')}) on :5002")
    app.run(host="0.0.0.0", port=5002, debug=True)
