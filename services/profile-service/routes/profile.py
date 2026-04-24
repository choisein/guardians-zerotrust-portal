"""
routes/profile.py - 학적조회 엔드포인트
───────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/profile
OPA 정책 패키지: guardians/profile
"""

from flask import Blueprint, request, jsonify, session

from shared.models import StudentProfile
from shared.middleware import zero_trust_required

profile_bp = Blueprint("profile", __name__, url_prefix="/api/student")


def _resolve_student_id():
    """관리자는 ?student_id=, 학생은 본인."""
    user_id = session.get("user_id")
    role = session.get("role")

    requested_id = request.args.get("student_id", type=int)

    if role == "admin":
        if not requested_id:
            return None, (jsonify({"error": "관리자는 student_id 파라미터가 필요합니다."}), 400)
        return requested_id, None

    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None, (jsonify({"error": "학생 프로필을 찾을 수 없습니다."}), 404)
    if requested_id and requested_id != profile.student_id:
        return None, (jsonify({"error": "본인의 정보만 조회할 수 있습니다."}), 403)
    return profile.student_id, None


@profile_bp.route("/profile", methods=["GET"])
@zero_trust_required(policy_package="guardians/profile")
def get_profile():
    student_id, err = _resolve_student_id()
    if err:
        return err
    profile = StudentProfile.query.get(student_id)
    if not profile:
        return jsonify({"error": "학생 정보를 찾을 수 없습니다."}), 404
    return jsonify(profile.to_dict()), 200
