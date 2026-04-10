"""
routes/student.py - 학생 정보 관련 API 라우트
──────────────────────────────────────────────
역할: 로그인한 학생의 프로필, 성적, 수강내역, 등록금 정보를 조회합니다.
      관리자는 학번을 지정하여 다른 학생의 정보도 조회할 수 있습니다.

엔드포인트:
  GET /api/student/profile               - 학생 기본 정보 조회
  GET /api/student/grades                 - 전체 성적 조회
  GET /api/student/grades/<semester>      - 특정 학기 성적 조회
  GET /api/student/enrollments            - 현재 수강 내역 조회
  GET /api/student/registrations          - 등록금 납부 내역 조회

공통 쿼리 파라미터:
  ?student_id=202300001   (관리자 전용 - 특정 학생 지정)

인증:
  모든 엔드포인트는 로그인 상태(세션)를 확인합니다.
  학생은 본인 정보만 조회 가능하고, 관리자는 모든 학생 정보를 조회할 수 있습니다.
"""

from flask import Blueprint, request, jsonify, session
from models import db, StudentProfile, Enrollment, Registration, Grade

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


def _get_student_id():
    """
    요청에서 조회 대상 학번을 결정하는 헬퍼 함수.

    - 학생: 본인 세션에서 학번을 가져옴
    - 관리자: 쿼리 파라미터 student_id 사용 가능

    Returns:
        (student_id: int, error_response: tuple | None)
    """
    user_id = session.get("user_id")
    role = session.get("role")

    if not user_id:
        return None, (jsonify({"error": "로그인이 필요합니다."}), 401)

    # 관리자가 특정 학생을 지정한 경우
    requested_id = request.args.get("student_id", type=int)

    if role == "admin":
        if not requested_id:
            return None, (jsonify({"error": "관리자는 student_id 파라미터가 필요합니다."}), 400)
        return requested_id, None

    # 학생: 본인 프로필에서 학번 조회
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None, (jsonify({"error": "학생 프로필을 찾을 수 없습니다."}), 404)

    # 학생이 다른 학생의 정보를 요청하는 것을 차단
    if requested_id and requested_id != profile.student_id:
        return None, (jsonify({"error": "본인의 정보만 조회할 수 있습니다."}), 403)

    return profile.student_id, None


# ─────────────────────────────────────────────
# 1. 학생 프로필 조회
# ─────────────────────────────────────────────
@student_bp.route("/profile", methods=["GET"])
def get_profile():
    """
    학생 기본 정보를 반환합니다.
    이름, 학번, 전공, 학기, 재학상태, 연락처 등을 포함합니다.
    """
    student_id, err = _get_student_id()
    if err:
        return err

    profile = StudentProfile.query.get(student_id)
    if not profile:
        return jsonify({"error": "학생 정보를 찾을 수 없습니다."}), 404

    return jsonify(profile.to_dict()), 200


# ─────────────────────────────────────────────
# 2. 성적 조회
# ─────────────────────────────────────────────
@student_bp.route("/grades", methods=["GET"])
def get_grades():
    """
    전체 학기 성적을 학기별로 그룹핑하여 반환합니다.

    응답 형식:
    {
      "student_id": 202300001,
      "avg_grade": 3.39,
      "semesters": {
        "1": { "semester_grade": 3.42, "courses": [...] },
        "2": { ... }
      }
    }
    """
    student_id, err = _get_student_id()
    if err:
        return err

    grades = Grade.query.filter_by(student_id=student_id)\
                        .order_by(Grade.semester, Grade.course_name).all()

    if not grades:
        return jsonify({"student_id": student_id, "avg_grade": 0, "semesters": {}}), 200

    # 학기별 그룹핑
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


@student_bp.route("/grades/<int:semester>", methods=["GET"])
def get_grades_by_semester(semester):
    """
    특정 학기의 성적만 반환합니다.
    """
    student_id, err = _get_student_id()
    if err:
        return err

    grades = Grade.query.filter_by(student_id=student_id, semester=semester)\
                        .order_by(Grade.course_name).all()

    return jsonify({
        "student_id": student_id,
        "semester": semester,
        "courses": [g.to_dict() for g in grades],
    }), 200


# ─────────────────────────────────────────────
# 3. 수강 내역 조회
# ─────────────────────────────────────────────
@student_bp.route("/enrollments", methods=["GET"])
def get_enrollments():
    """
    현재 학기 수강 과목 목록을 반환합니다.
    과목명, 담당교수, 현재 성적(미정이면 0)을 포함합니다.
    """
    student_id, err = _get_student_id()
    if err:
        return err

    enrollments = Enrollment.query.filter_by(student_id=student_id)\
                                  .order_by(Enrollment.course_name).all()

    return jsonify({
        "student_id": student_id,
        "enrollments": [e.to_dict() for e in enrollments],
    }), 200


# ─────────────────────────────────────────────
# 4. 등록금 납부 내역 조회
# ─────────────────────────────────────────────
@student_bp.route("/registrations", methods=["GET"])
def get_registrations():
    """
    등록금 납부 내역을 반환합니다.
    납부 상태(완료/미납/분할납부), 금액, 등록일 등을 포함합니다.
    """
    student_id, err = _get_student_id()
    if err:
        return err

    registrations = Registration.query.filter_by(student_id=student_id)\
                                      .order_by(Registration.reg_date.desc()).all()

    return jsonify({
        "student_id": student_id,
        "registrations": [r.to_dict() for r in registrations],
    }), 200