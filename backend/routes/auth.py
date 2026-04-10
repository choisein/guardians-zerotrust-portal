"""
routes/auth.py - 인증 관련 API 라우트
──────────────────────────────────────
역할: 로그인, 로그아웃, 세션 확인 기능을 제공합니다.

엔드포인트:
  POST /api/auth/login   - 사용자 로그인 (user_id + password)
  POST /api/auth/logout  - 로그아웃 (세션 제거)
  GET  /api/auth/session  - 현재 로그인 상태 확인

보안:
  - 비밀번호는 SHA-256 해시로 비교합니다 (DB에 이미 해시로 저장됨).
  - 로그인 성공 시 Flask 세션에 user_id와 role을 저장합니다.
  - 제로 트러스트 원칙에 따라, 매 요청마다 세션 유효성을 확인해야 합니다.
"""

import hashlib
from flask import Blueprint, request, jsonify, session
from models import db, User, StudentProfile

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    로그인 API
    ──────────
    요청 body (JSON):
      { "user_id": "user_202300001", "password": "plaintext_password" }

    성공 응답 (200):
      { "message": "로그인 성공", "user": { ... }, "profile": { ... } }

    실패 응답 (401):
      { "error": "아이디 또는 비밀번호가 일치하지 않습니다." }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "요청 데이터가 없습니다."}), 400

    user_id = data.get("user_id", "").strip()
    password = data.get("password", "").strip()

    if not user_id or not password:
        return jsonify({"error": "아이디와 비밀번호를 모두 입력해주세요."}), 400

    # SHA-256 해시 비교
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    user = User.query.filter_by(user_id=user_id).first()

    if not user or user.password != password_hash:
        return jsonify({"error": "아이디 또는 비밀번호가 일치하지 않습니다."}), 401

    # 세션에 사용자 정보 저장
    session["user_id"] = user.user_id
    session["role"] = user.role

    # 학생이면 프로필도 함께 반환
    profile_data = None
    if user.role == "student" and user.profile:
        profile_data = user.profile.to_dict()

    return jsonify({
        "message": "로그인 성공",
        "user": user.to_dict(),
        "profile": profile_data,
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    로그아웃 API
    ────────────
    세션을 완전히 삭제합니다.
    """
    session.clear()
    return jsonify({"message": "로그아웃 완료"}), 200


@auth_bp.route("/session", methods=["GET"])
def check_session():
    """
    세션 확인 API
    ─────────────
    현재 로그인된 사용자의 정보를 반환합니다.
    로그인되지 않았으면 401을 반환합니다.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "유효하지 않은 세션입니다."}), 401

    profile_data = None
    if user.role == "student" and user.profile:
        profile_data = user.profile.to_dict()

    return jsonify({
        "user": user.to_dict(),
        "profile": profile_data,
    }), 200