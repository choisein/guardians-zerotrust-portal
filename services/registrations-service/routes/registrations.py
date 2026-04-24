"""
routes/registrations.py - 등록금납부조회 엔드포인트
───────────────────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/registrations
OPA 정책 패키지: guardians/registrations
"""

from flask import Blueprint, request, jsonify, session

from shared.models import Registration, StudentProfile
from shared.middleware import zero_trust_required

registrations_bp = Blueprint("registrations", __name__, url_prefix="/api/student")


def _resolve_student_id():
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


@registrations_bp.route("/registrations", methods=["GET"])
@zero_trust_required(policy_package="guardians/registrations")
def get_registrations():
    student_id, err = _resolve_student_id()
    if err:
        return err

    registrations = Registration.query.filter_by(student_id=student_id)\
                                      .order_by(Registration.reg_date.desc()).all()
    return jsonify({
        "student_id": student_id,
        "registrations": [r.to_dict() for r in registrations],
    }), 200
