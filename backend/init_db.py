"""
init_db.py - 데이터베이스 초기화 스크립트
실행: cd backend && python init_db.py
"""

import hashlib
import os
import re
from datetime import date
from app import create_app
from models import db, User, StudentProfile, Enrollment, Registration, Grade


def parse_values(sql):
    """INSERT 문에서 VALUES(...) 안의 값들을 파싱"""
    match = re.search(r"VALUES\s*\((.+)\)\s*;?\s*$", sql, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1)
    values = []
    current = ""
    in_string = False
    for ch in raw:
        if ch == "'" and (not current or current[-1] != "\\"):
            in_string = not in_string
        elif ch == "," and not in_string:
            values.append(current.strip().strip("'"))
            current = ""
            continue
        current += ch
    values.append(current.strip().strip("'"))
    return values


def init():
    app = create_app()

    with app.app_context():
        db.create_all()

        if User.query.first():
            print("⚠️  데이터가 이미 존재합니다.")
            print("   초기화하려면 backend/portal.db 삭제 후 다시 실행하세요.")
            return

        print("📦 샘플 데이터 로딩 중...")

        sql_path = os.path.join(os.path.dirname(__file__), "..", "db", "portal_db.sql")

        if not os.path.exists(sql_path):
            print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_path}")
            return

        with open(sql_path, "r", encoding="utf-8") as f:
            content = f.read()

        insert_lines = []
        for line in content.split("\n"):
            line = line.strip()
            if line.upper().startswith("INSERT INTO"):
                insert_lines.append(line)

        user_inserts = [l for l in insert_lines if "INSERT INTO user " in l]
        profile_inserts = [l for l in insert_lines if "INSERT INTO student_profile" in l]
        enrollment_inserts = [l for l in insert_lines if "INSERT INTO enrollment" in l]
        registration_inserts = [l for l in insert_lines if "INSERT INTO registration" in l]
        grade_inserts = [l for l in insert_lines if "INSERT INTO grade" in l]

        # 1. User
        for sql in user_inserts:
            vals = parse_values(sql)
            if vals:
                db.session.add(User(user_id=vals[0], password=vals[1], role=vals[2]))
        db.session.commit()
        print(f"  ✅ user: {len(user_inserts)}건")

        # 2. StudentProfile
        for sql in profile_inserts:
            vals = parse_values(sql)
            if vals:
                db.session.add(StudentProfile(
                    user_id=vals[0],
                    student_id=int(vals[1]),
                    name=vals[2],
                    phone=vals[3] if vals[3] != "NULL" else None,
                    email_add=vals[4] if vals[4] != "NULL" else None,
                    major=vals[5] if vals[5] != "NULL" else None,
                    current_semester=int(vals[6]),
                    status=vals[7],
                ))
        db.session.commit()
        print(f"  ✅ student_profile: {len(profile_inserts)}건")

        # 3. Enrollment
        for sql in enrollment_inserts:
            vals = parse_values(sql)
            if vals:
                db.session.add(Enrollment(
                    student_id=int(vals[0]),
                    current_semester=int(vals[1]),
                    course_name=vals[2],
                    course_professor=vals[3] if vals[3] != "NULL" else None,
                    course_grade=float(vals[4]) if vals[4] != "NULL" else None,
                ))
        db.session.commit()
        print(f"  ✅ enrollment: {len(enrollment_inserts)}건")

        # 4. Registration
        for sql in registration_inserts:
            vals = parse_values(sql)
            if vals:
                db.session.add(Registration(
                    student_id=int(vals[0]),
                    reg_status=vals[1],
                    status=vals[2],
                    paid_amount=int(vals[3]),
                    reg_date=date.fromisoformat(vals[4]) if vals[4] != "NULL" else None,
                ))
        db.session.commit()
        print(f"  ✅ registration: {len(registration_inserts)}건")

        # 5. Grade
        for sql in grade_inserts:
            vals = parse_values(sql)
            if vals:
                db.session.add(Grade(
                    student_id=int(vals[0]),
                    semester=int(vals[1]),
                    course_name=vals[2],
                    course_grade=float(vals[3]) if vals[3] != "NULL" else None,
                    semester_grade=float(vals[4]) if vals[4] != "NULL" else None,
                    avg_grade=float(vals[5]) if vals[5] != "NULL" else None,
                ))
        db.session.commit()
        print(f"  ✅ grade: {len(grade_inserts)}건")

        # 테스트 계정 비밀번호 설정 (test1234)
        test_pw = hashlib.sha256("test1234".encode()).hexdigest()
        for uid in ["user_202300001", "user_201800002", "user_201800003", "user_202300004", "admin_001"]:
            u = User.query.get(uid)
            if u:
                u.password = test_pw
        db.session.commit()

        print()
        print("=" * 50)
        print("🎉 데이터베이스 초기화 완료!")
        print()
        print("🔑 테스트 계정:")
        print("  학생:   user_202300001 / test1234")
        print("  관리자: admin_001 / test1234")
        print("=" * 50)


if __name__ == "__main__":
    init()