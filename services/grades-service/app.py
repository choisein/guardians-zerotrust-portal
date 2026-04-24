"""
grades-service / app.py - 성적조회 서비스
─────────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/grades
역할: 전체/학기별 성적 조회

엔드포인트:
  GET /api/student/grades
  GET /api/student/grades/<semester>

포트: 5003
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

sys.path.insert(0, "/app")

from shared.models import db
from shared.config import BaseConfig
from routes.grades import grades_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    db.init_app(app)
    CORS(app, supports_credentials=True)

    app.register_blueprint(grades_bp)

    @app.route("/health")
    def health():
        return jsonify({
            "service": "grades-service",
            "spiffe_id": os.environ.get("SERVICE_SPIFFE_ID"),
            "status": "ok",
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    print(f"📊 Grades Service (SPIFFE: {os.environ.get('SERVICE_SPIFFE_ID')}) on :5003")
    app.run(host="0.0.0.0", port=5003, debug=True)
