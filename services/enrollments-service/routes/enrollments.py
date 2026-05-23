"""
routes/enrollments.py - 수강내역조회 엔드포인트
───────────────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/enrollments
OPA 정책 패키지: guardians/enrollments
"""

from flask import Blueprint, request, jsonify, session

from shared.models import Enrollment, StudentProfile
from shared.middleware import zero_trust_required
from shared.service_client import call_service, response_summary

enrollments_bp = Blueprint("enrollments", __name__, url_prefix="/api/student")


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


@enrollments_bp.route("/enrollments", methods=["GET"])
@zero_trust_required(policy_package="guardians/enrollments")
def get_enrollments():
    student_id, err = _resolve_student_id()
    if err:
        return err

    enrollments = Enrollment.query.filter_by(student_id=student_id)\
                                  .order_by(Enrollment.course_name).all()
    return jsonify({
        "student_id": student_id,
        "enrollments": [e.to_dict() for e in enrollments],
    }), 200


# ──────────────────────────────────────────────────────────────
# [데모] 서비스 간 직접 호출 — 허용된 호출 (allow)
# enrollments 는 선수과목 확인을 위해 grades 를, 수강 자격 확인을 위해
# profile 을 호출할 수 있다 (호출 그래프상 허용 엣지, 읽기만).
# ──────────────────────────────────────────────────────────────
@enrollments_bp.route("/enrollments/internal/grades", methods=["GET"])
@zero_trust_required(policy_package="guardians/enrollments")
def demo_enrollments_calls_grades():
    resp = call_service("grades", "/api/student/grades", cookies=request.cookies)
    status = resp.status_code if resp is not None else 502
    return jsonify({
        "demo": "enrollments -> grades (선수과목 확인)",
        "expected": "허용 엣지 → allow (정상 조회)",
        "downstream": response_summary(resp),
    }), status


@enrollments_bp.route("/enrollments/internal/profile", methods=["GET"])
@zero_trust_required(policy_package="guardians/enrollments")
def demo_enrollments_calls_profile():
    resp = call_service("profile", "/api/student/profile", cookies=request.cookies)
    status = resp.status_code if resp is not None else 502
    return jsonify({
        "demo": "enrollments -> profile (수강 자격 확인)",
        "expected": "허용 엣지 → allow (정상 조회)",
        "downstream": response_summary(resp),
    }), status
