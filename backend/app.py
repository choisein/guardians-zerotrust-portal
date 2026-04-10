import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from models import db


def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(base_dir, "..", "frontend")
    frontend_dir = os.path.normpath(frontend_dir)

    print(f"📂 프론트엔드 경로: {frontend_dir}")
    print(f"   존재 여부: {os.path.exists(frontend_dir)}")

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app, supports_credentials=True)

    from routes.auth import auth_bp
    from routes.student import student_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)

    @app.route("/")
    def index():
        return send_from_directory(os.path.join(frontend_dir, "templates"), "login.html")

    @app.route("/templates/<path:filename>")
    def serve_template(filename):
        return send_from_directory(os.path.join(frontend_dir, "templates"), filename)

    @app.route("/static/css/<path:filename>")
    def serve_css_static(filename):
        return send_from_directory(os.path.join(frontend_dir, "css"), filename)

    @app.route("/static/js/<path:filename>")
    def serve_js_static(filename):
        return send_from_directory(os.path.join(frontend_dir, "js"), filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(os.path.join(frontend_dir, "css"), filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(os.path.join(frontend_dir, "js"), filename)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ DB 테이블 준비 완료")
    print("=" * 50)
    print("🚀 서버 시작: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)