import csv

def esc(val):
    if val is None or val.strip() == '':
        return 'NULL'
    return "'" + val.replace("'", "''") + "'"

files = {
    'user.csv': 'utf-8-sig',
    'student_profile.csv': 'cp949',
    'enrollment.csv': 'cp949',
    'registrarion.csv': 'cp949',
    'grade.csv': 'cp949'
}
base = 'C:/Users/user/Desktop/26캡스톤/db/'
out_path = base + 'create_db.sql'

data = {}
for f, enc in files.items():
    with open(base + f, encoding=enc, errors='replace') as fp:
        reader = csv.DictReader(fp)
        data[f] = list(reader)

lines = []
lines.append("-- ============================================================")
lines.append("-- 데이터베이스 생성 SQL")
lines.append("-- 생성일: 2026-04-05")
lines.append("-- ============================================================")
lines.append("")
lines.append("CREATE DATABASE IF NOT EXISTS capstone_db")
lines.append("    CHARACTER SET utf8mb4")
lines.append("    COLLATE utf8mb4_unicode_ci;")
lines.append("")
lines.append("USE capstone_db;")
lines.append("")

# ── 1. user ──
lines.append("-- ============================================================")
lines.append("-- 1. user 테이블")
lines.append("-- ============================================================")
lines.append("CREATE TABLE IF NOT EXISTS user (")
lines.append("    user_id     VARCHAR(20)  NOT NULL COMMENT '사용자 ID',")
lines.append("    password    VARCHAR(64)  NOT NULL COMMENT '비밀번호 (SHA-256 해시)',")
lines.append("    role        ENUM('student', 'admin') NOT NULL DEFAULT 'student' COMMENT '사용자 권한',")
lines.append("    PRIMARY KEY (user_id)")
lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='사용자 계정';")
lines.append("")

# ── 2. student_profile ──
lines.append("-- ============================================================")
lines.append("-- 2. student_profile 테이블")
lines.append("-- ============================================================")
lines.append("CREATE TABLE IF NOT EXISTS student_profile (")
lines.append("    user_id          VARCHAR(20)      NOT NULL COMMENT '사용자 ID (FK)',")
lines.append("    student_id       INT              NOT NULL COMMENT '학번',")
lines.append("    name             VARCHAR(50)      NOT NULL COMMENT '이름',")
lines.append("    phone            VARCHAR(20)          NULL COMMENT '전화번호',")
lines.append("    email_add        VARCHAR(100)         NULL COMMENT '이메일',")
lines.append("    major            VARCHAR(50)          NULL COMMENT '전공',")
lines.append("    current_semester TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '현재 학기',")
lines.append("    status           VARCHAR(10)      NOT NULL COMMENT '재학 상태 (재학/휴학)',")
lines.append("    PRIMARY KEY (student_id),")
lines.append("    UNIQUE  KEY uq_sp_user_id (user_id),")
lines.append("    CONSTRAINT fk_sp_user FOREIGN KEY (user_id) REFERENCES user(user_id)")
lines.append("        ON UPDATE CASCADE ON DELETE CASCADE")
lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='학생 프로필';")
lines.append("")

# ── 3. enrollment ──
lines.append("-- ============================================================")
lines.append("-- 3. enrollment 테이블")
lines.append("-- ============================================================")
lines.append("CREATE TABLE IF NOT EXISTS enrollment (")
lines.append("    id               BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT 'PK',")
lines.append("    student_id       INT              NOT NULL COMMENT '학번 (FK)',")
lines.append("    current_semester TINYINT UNSIGNED NOT NULL COMMENT '수강 학기',")
lines.append("    course_name      VARCHAR(100)     NOT NULL COMMENT '과목명',")
lines.append("    course_professor VARCHAR(50)          NULL COMMENT '담당 교수',")
lines.append("    course_grade     DECIMAL(3,1)         NULL COMMENT '과목 성적',")
lines.append("    PRIMARY KEY (id),")
lines.append("    CONSTRAINT fk_enr_student FOREIGN KEY (student_id) REFERENCES student_profile(student_id)")
lines.append("        ON UPDATE CASCADE ON DELETE CASCADE")
lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='수강 내역';")
lines.append("")

# ── 4. registration ──
lines.append("-- ============================================================")
lines.append("-- 4. registration 테이블  (원본 파일명: registrarion.csv)")
lines.append("-- ============================================================")
lines.append("CREATE TABLE IF NOT EXISTS registration (")
lines.append("    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'PK',")
lines.append("    student_id   INT             NOT NULL COMMENT '학번 (FK)',")
lines.append("    reg_status   VARCHAR(20)     NOT NULL COMMENT '등록 처리 상태 (완료/미납/취소대기)',")
lines.append("    status       VARCHAR(10)     NOT NULL COMMENT '재학 상태',")
lines.append("    paid_amount  INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '납부 금액',")
lines.append("    reg_date     DATE                NULL COMMENT '등록일',")
lines.append("    PRIMARY KEY (id),")
lines.append("    CONSTRAINT fk_reg_student FOREIGN KEY (student_id) REFERENCES student_profile(student_id)")
lines.append("        ON UPDATE CASCADE ON DELETE CASCADE")
lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='등록 정보';")
lines.append("")

# ── 5. grade ──
lines.append("-- ============================================================")
lines.append("-- 5. grade 테이블")
lines.append("-- ============================================================")
lines.append("CREATE TABLE IF NOT EXISTS grade (")
lines.append("    id             BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT 'PK',")
lines.append("    student_id     INT              NOT NULL COMMENT '학번 (FK)',")
lines.append("    semester       TINYINT UNSIGNED NOT NULL COMMENT '학기',")
lines.append("    course_name    VARCHAR(100)     NOT NULL COMMENT '과목명',")
lines.append("    course_grade   DECIMAL(3,1)         NULL COMMENT '과목 성적',")
lines.append("    semester_grade DECIMAL(4,2)         NULL COMMENT '학기 평균 성적',")
lines.append("    avg_grade      DECIMAL(4,2)         NULL COMMENT '전체 평균 성적',")
lines.append("    PRIMARY KEY (id),")
lines.append("    CONSTRAINT fk_grade_student FOREIGN KEY (student_id) REFERENCES student_profile(student_id)")
lines.append("        ON UPDATE CASCADE ON DELETE CASCADE")
lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='성적 정보';")
lines.append("")

# ── INSERT: user ──
lines.append("-- ============================================================")
lines.append("-- INSERT: user")
lines.append("-- ============================================================")
for r in data['user.csv']:
    lines.append(
        "INSERT INTO user (user_id, password, role) VALUES ("
        + esc(r['user_id']) + ", " + esc(r['password']) + ", " + esc(r['role']) + ");"
    )
lines.append("")

# ── INSERT: student_profile ──
lines.append("-- ============================================================")
lines.append("-- INSERT: student_profile")
lines.append("-- ============================================================")
for r in data['student_profile.csv']:
    lines.append(
        "INSERT INTO student_profile (user_id, student_id, name, phone, email_add, major, current_semester, status) VALUES ("
        + esc(r['user_id']) + ", " + r['student_id'] + ", " + esc(r['name']) + ", "
        + esc(r['phone']) + ", " + esc(r['email_add']) + ", " + esc(r['major']) + ", "
        + r['current_semester'] + ", " + esc(r['status']) + ");"
    )
lines.append("")

# ── INSERT: enrollment ──
lines.append("-- ============================================================")
lines.append("-- INSERT: enrollment")
lines.append("-- ============================================================")
for r in data['enrollment.csv']:
    grade_val = r['course_grade'].strip()
    grade_sql = 'NULL' if grade_val == '' else grade_val
    lines.append(
        "INSERT INTO enrollment (student_id, current_semester, course_name, course_professor, course_grade) VALUES ("
        + r['sudent_id'] + ", " + r['current_semester'] + ", "
        + esc(r['course_name']) + ", " + esc(r['course_professor']) + ", " + grade_sql + ");"
    )
lines.append("")

# ── INSERT: registration ──
lines.append("-- ============================================================")
lines.append("-- INSERT: registration")
lines.append("-- ============================================================")
for r in data['registrarion.csv']:
    lines.append(
        "INSERT INTO registration (student_id, reg_status, status, paid_amount, reg_date) VALUES ("
        + r['student_id'] + ", " + esc(r['reg_status']) + ", " + esc(r['status']) + ", "
        + r['paid_amount'] + ", " + esc(r['reg_date']) + ");"
    )
lines.append("")

# ── INSERT: grade ──
lines.append("-- ============================================================")
lines.append("-- INSERT: grade")
lines.append("-- ============================================================")
for r in data['grade.csv']:
    cg = r['course_grade'].strip() or 'NULL'
    sg = r['semester_grade'].strip() or 'NULL'
    ag = r['avg_grade'].strip() or 'NULL'
    lines.append(
        "INSERT INTO grade (student_id, semester, course_name, course_grade, semester_grade, avg_grade) VALUES ("
        + r['student_id'] + ", " + r['semester'] + ", " + esc(r['course_name']) + ", "
        + cg + ", " + sg + ", " + ag + ");"
    )
lines.append("")

sql_text = "\n".join(lines)
with open(out_path, 'w', encoding='utf-8') as fp:
    fp.write(sql_text)

print("완료! 총 라인 수:", len(lines))
print("파일 저장:", out_path)
