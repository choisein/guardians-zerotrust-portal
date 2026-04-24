"""
enrollments-service / app.py - 수강내역조회 서비스
──────────────────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/enrollments
역할: 현재 학기 수강 과목 조회

엔드포인트:
  GET /api/student/enrollments

포트: 5004
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

sys.path.insert(0, "/app")

from shared.models import db
from shared.config import BaseConfig
from routes.enrollments import enrollments_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    db.init_app(app)
    CORS(app, supports_credentials=True)

    app.register_blueprint(enrollments_bp)

    @app.route("/health")
    def health():
        return jsonify({
            "service": "enrollments-service",
            "spiffe_id": os.environ.get("SERVICE_SPIFFE_ID"),
            "status": "ok",
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    print(f"📚 Enrollments Service (SPIFFE: {os.environ.get('SERVICE_SPIFFE_ID')}) on :5004")
    app.run(host="0.0.0.0", port=5004, debug=True)
