"""
routes/grades.py - 성적조회 엔드포인트
──────────────────────────────────────
SPIFFE ID: spiffe://guardians.local/service/grades
OPA 정책 패키지: guardians/grades
"""

from flask import Blueprint, request, jsonify, session

from shared.models import Grade, StudentProfile
from shared.middleware import zero_trust_required

grades_bp = Blueprint("grades", __name__, url_prefix="/api/student")


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


@grades_bp.route("/grades", methods=["GET"])
@zero_trust_required(policy_package="guardians/grades")
def get_grades():
    student_id, err = _resolve_student_id()
    if err:
        return err

    grades = Grade.query.filter_by(student_id=student_id)\
                        .order_by(Grade.semester, Grade.course_name).all()
    if not grades:
        return jsonify({"student_id": student_id, "avg_grade": 0, "semesters": {}}), 200

    semesters = {}
    overall_avg = None
    for g in grades:
        sem = str(g.semester)
        if sem not in semesters:
            semesters[sem] = {
                "semester_grade": float(g.semester_grade) if g.semester_grade else 0,
                "courses": [],
            }
        semesters[sem]["courses"].append({
            "course_name": g.course_name,
            "course_grade": float(g.course_grade) if g.course_grade is not None else None,
        })
        if g.avg_grade is not None:
            overall_avg = float(g.avg_grade)

    return jsonify({
        "student_id": student_id,
        "avg_grade": overall_avg,
        "semesters": semesters,
    }), 200


@grades_bp.route("/grades/<int:semester>", methods=["GET"])
@zero_trust_required(policy_package="guardians/grades")
def get_grades_by_semester(semester):
    student_id, err = _resolve_student_id()
    if err:
        return err

    grades = Grade.query.filter_by(student_id=student_id, semester=semester)\
                        .order_by(Grade.course_name).all()
    return jsonify({
        "student_id": student_id,
        "semester": semester,
        "courses": [g.to_dict() for g in grades],
    }), 200
