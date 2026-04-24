"""
shared/config.py - 공통 설정
────────────────────────────
환경변수 기반으로 DB, 세션, SPIRE, OPA 주소를 설정합니다.
각 서비스의 config.py는 이 파일을 상속하거나 참조합니다.
"""

import os


class BaseConfig:
    # Flask 기본 설정
    SECRET_KEY = os.environ.get("SECRET_KEY", "guardians-dev-secret-key")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # DB 설정 (기본: SQLite, MySQL 전환 가능)
    USE_MYSQL = os.environ.get("USE_MYSQL", "false").lower() == "true"
    if USE_MYSQL:
        DB_USER = os.environ.get("DB_USER", "guardians")
        DB_PASS = os.environ.get("DB_PASS", "guardians")
        DB_HOST = os.environ.get("DB_HOST", "db")
        DB_PORT = os.environ.get("DB_PORT", "3306")
        DB_NAME = os.environ.get("DB_NAME", "portal_db")
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL",
            f"sqlite:////data/portal.db",
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SPIRE 워크로드 API 소켓 (Unix Domain Socket)
    SPIRE_SOCKET_PATH = os.environ.get(
        "SPIRE_AGENT_SOCKET", "unix:///tmp/spire-agent/public/api.sock"
    )

    # SPIFFE ID (서비스별로 주입)
    SERVICE_SPIFFE_ID = os.environ.get("SERVICE_SPIFFE_ID", "")

    # OPA 서버 주소
    OPA_URL = os.environ.get("OPA_URL", "http://opa:8181")

    # 현재 서비스명 (OPA 정책 질의 시 사용)
    SERVICE_NAME = os.environ.get("SERVICE_NAME", "unknown")
