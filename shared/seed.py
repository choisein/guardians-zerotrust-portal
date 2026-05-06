"""
shared/seed.py - 초기 시드 데이터 적재 (도커 환경 자동 실행)
─────────────────────────────────────────────────────────────
auth-service 가 기동할 때 User 테이블이 비어있으면 호출되어,
db/portal_db.sql 안의 INSERT 문을 파싱해 SQLAlchemy 로 일괄 삽입한다.

이 모듈은 backend/init_db.py 의 로직을 그대로 옮긴 뒤
컨테이너용 shared 모델 (shared.models) 을 쓰도록 정리한 것이다.

테스트 계정 5개의 비밀번호는 모두 sha256("test1234") 로 덮어쓴다:
  user_202300001, user_201800002, user_201800003, user_202300004, admin_001
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import date
from typing import Iterable, List, Optional

from .models import db, User, StudentProfile, Enrollment, Registration, Grade

logger = logging.getLogger(__name__)


SQL_FILE_CANDIDATES = (
    "/app/db/portal_db.sql",          # 컨테이너 안 표준 위치
    "/db/portal_db.sql",
    os.path.join(os.path.dirname(__file__), "..", "db", "portal_db.sql"),
)

TEST_PASSWORD = "test1234"
TEST_ACCOUNTS = (
    "user_202300001",
    "user_201800002",
    "user_201800003",
    "user_202300004",
    "admin_001",
)


def _find_sql_file() -> Optional[str]:
    for p in SQL_FILE_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _parse_values(sql: str) -> Optional[List[str]]:
    """`INSERT INTO ... VALUES (...);` 의 괄호 안 값들을 콤마로 분리."""
    m = re.search(r"VALUES\s*\((.+)\)\s*;?\s*$", sql, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1)
    values: List[str] = []
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


def _filter_inserts(content: str, table: str) -> Iterable[str]:
    needle = f"INSERT INTO {table} ".lower()
    for line in content.split("\n"):
        line = line.strip()
        if line.lower().startswith(needle):
            yield line


def seed_if_empty() -> bool:
    """User 테이블이 비어있을 때만 시드. 시드를 수행하면 True 반환."""
    if db.session.query(User).first() is not None:
        logger.info("seed: 기존 데이터 발견, 시드 스킵")
        return False

    sql_path = _find_sql_file()
    if not sql_path:
        logger.warning("seed: SQL 파일을 찾을 수 없어 최소 테스트 계정만 생성")
        _seed_minimal()
        return True

    logger.info("seed: %s 에서 데이터 로딩", sql_path)
    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()

    # User
    n_user = 0
    for sql in _filter_inserts(content, "user"):
        v = _parse_values(sql)
        if v:
            db.session.add(User(user_id=v[0], password=v[1], role=v[2]))
            n_user += 1
    db.session.commit()
    logger.info("seed: user %d건", n_user)

    # StudentProfile
    n_prof = 0
    for sql in _filter_inserts(content, "student_profile"):
        v = _parse_values(sql)
        if v:
            db.session.add(StudentProfile(
                user_id=v[0],
                student_id=int(v[1]),
                name=v[2],
                phone=None if v[3] == "NULL" else v[3],
                email_add=None if v[4] == "NULL" else v[4],
                major=None if v[5] == "NULL" else v[5],
                current_semester=int(v[6]),
                status=v[7],
            ))
            n_prof += 1
    db.session.commit()
    logger.info("seed: student_profile %d건", n_prof)

    # Enrollment
    n_enr = 0
    for sql in _filter_inserts(content, "enrollment"):
        v = _parse_values(sql)
        if v:
            db.session.add(Enrollment(
                student_id=int(v[0]),
                current_semester=int(v[1]),
                course_name=v[2],
                course_professor=None if v[3] == "NULL" else v[3],
                course_grade=None if v[4] == "NULL" else float(v[4]),
            ))
            n_enr += 1
    db.session.commit()
    logger.info("seed: enrollment %d건", n_enr)

    # Registration
    n_reg = 0
    for sql in _filter_inserts(content, "registration"):
        v = _parse_values(sql)
        if v:
            db.session.add(Registration(
                student_id=int(v[0]),
                reg_status=v[1],
                status=v[2],
                paid_amount=int(v[3]),
                reg_date=date.fromisoformat(v[4]) if v[4] != "NULL" else None,
            ))
            n_reg += 1
    db.session.commit()
    logger.info("seed: registration %d건", n_reg)

    # Grade
    n_grade = 0
    for sql in _filter_inserts(content, "grade"):
        v = _parse_values(sql)
        if v:
            db.session.add(Grade(
                student_id=int(v[0]),
                semester=int(v[1]),
                course_name=v[2],
                course_grade=None if v[3] == "NULL" else float(v[3]),
                semester_grade=None if v[4] == "NULL" else float(v[4]),
                avg_grade=None if v[5] == "NULL" else float(v[5]),
            ))
            n_grade += 1
    db.session.commit()
    logger.info("seed: grade %d건", n_grade)

    # 테스트 계정 비밀번호 통일
    test_pw = hashlib.sha256(TEST_PASSWORD.encode("utf-8")).hexdigest()
    for uid in TEST_ACCOUNTS:
        u = db.session.get(User, uid)
        if u:
            u.password = test_pw
    db.session.commit()
    logger.info(
        "seed: 테스트 계정 비밀번호 = '%s' (계정 %d개 적용)",
        TEST_PASSWORD,
        len(TEST_ACCOUNTS),
    )

    return True


def _seed_minimal() -> None:
    """SQL 파일을 못 찾았을 때라도 로그인 테스트는 가능하도록 최소 계정만."""
    pw = hashlib.sha256(TEST_PASSWORD.encode("utf-8")).hexdigest()
    db.session.add(User(user_id="user_202300001", password=pw, role="student"))
    db.session.add(User(user_id="admin_001", password=pw, role="admin"))
    db.session.commit()
    logger.info("seed (fallback): user_202300001 / admin_001 만 생성")
