"""
routes/auth.py - 로그인/로그아웃/세션 확인
──────────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/auth
OPA 정책 패키지: guardians/auth

특이사항:
  - /login, /logout, /session 은 세션 없이도 호출되어야 하므로
    require_session=False 로 보호
  - 하지만 SVID 검증은 동일하게 수행 (게이트웨이만 호출 가능)
"""

import hashlib
from flask import Blueprint, request, jsonify, session

from shared.models import db, User
from shared.middleware import zero_trust_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
@zero_trust_required(policy_package="guardians/auth", require_session=False)
def login():
    data = request.get_json() or {}
    user_id = data.get("user_id", "").strip()
    password = data.get("password", "").strip()

    if not user_id or not password:
        return jsonify({"error": "아이디와 비밀번호를 모두 입력해주세요."}), 400

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    user = User.query.filter_by(user_id=user_id).first()

    if not user or user.password != password_hash:
        return jsonify({"error": "아이디 또는 비밀번호가 일치하지 않습니다."}), 401

    session["user_id"] = user.user_id
    session["role"] = user.role

    profile_data = None
    if user.role == "student" and user.profile:
        profile_data = user.profile.to_dict()

    return jsonify({
        "message": "로그인 성공",
        "user": user.to_dict(),
        "profile": profile_data,
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@zero_trust_required(policy_package="guardians/auth", require_session=False)
def logout():
    session.clear()
    return jsonify({"message": "로그아웃 완료"}), 200


@auth_bp.route("/session", methods=["GET"])
@zero_trust_required(policy_package="guardians/auth", require_session=False)
def check_session():
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

    return jsonify({"user": user.to_dict(), "profile": profile_data}), 200
