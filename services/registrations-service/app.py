"""
registrations-service / app.py - 등록금납부조회 서비스
──────────────────────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/registrations
역할: 등록금 납부 내역 조회

엔드포인트:
  GET /api/student/registrations

포트: 5005
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

sys.path.insert(0, "/app")

from shared.models import db
from shared.config import BaseConfig
from routes.registrations import registrations_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    db.init_app(app)
    CORS(app, supports_credentials=True)

    app.register_blueprint(registrations_bp)

    @app.route("/health")
    def health():
        return jsonify({
            "service": "registrations-service",
            "spiffe_id": os.environ.get("SERVICE_SPIFFE_ID"),
            "status": "ok",
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    print(f"💳 Registrations Service (SPIFFE: {os.environ.get('SERVICE_SPIFFE_ID')}) on :5005")
    app.run(host="0.0.0.0", port=5005, debug=True)
