"""
routes/profile.py - 학적조회 엔드포인트
───────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/profile
OPA 정책 패키지: guardians/profile
"""

from flask import Blueprint, request, jsonify, session

from shared.models import StudentProfile
from shared.middleware import zero_trust_required
from shared.service_client import call_service, response_summary

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


# ──────────────────────────────────────────────────────────────
# [데모] 서비스 간 직접 호출 — 횡적 이동(lateral movement) 시도
# profile 은 호출 그래프상 다른 서비스를 호출할 수 없는 leaf 이다.
# profile 이 grades 를 직접 호출하면 grades 의 OPA 가 critical_violation
# 으로 판정 → profile 의 SVID 가 즉시 폐지된다.
# ──────────────────────────────────────────────────────────────
@profile_bp.route("/profile/internal/grades", methods=["GET"])
@zero_trust_required(policy_package="guardians/profile")
def demo_profile_calls_grades():
    resp = call_service("grades", "/api/student/grades", cookies=request.cookies)
    status = resp.status_code if resp is not None else 502
    return jsonify({
        "demo": "profile -> grades (횡적 이동 시도)",
        "expected": "그래프 이탈 → critical_violation → profile SVID 즉시 폐지",
        "downstream": response_summary(resp),
    }), status
