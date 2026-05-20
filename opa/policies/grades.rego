# ──────────────────────────────────────────────────────────────
# grades.rego - 성적조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.grades
# 적용 라우트:
#   GET /api/student/grades
#   GET /api/student/grades/<semester>
# 민감도: 매우 높음 (성적은 가장 민감한 데이터)
#
# 정책 요약 (profile보다 엄격):
#   1) 게이트웨이를 통한 요청만 허용
#   2) 로그인된 사용자만 허용
#   3) GET 요청만 허용
#   4) 학생: 본인 성적만 조회 가능
#   5) 관리자: 모든 성적 조회 가능
#	6) 교수: 본인 교과목 학생 성적 입력, 조회 가능
#   7) 추가 보호: 비정상적 패턴 (대량 조회) 차단
#   8) critical_violation (신뢰 박탈 사유):
#        - 본인 외 학번의 성적 조회 시도
#        - 학생 권한으로 성적 변경(쓰기) 시도
#      → 미들웨어가 SPIRE entry 를 즉시 삭제
# ──────────────────────────────────────────────────────────────

package guardians.grades

import rego.v1
import data.guardians.common

default allow := false
default critical_violation := false

# 학생: 본인 성적만
allow if {
	common.is_from_gateway
	common.is_logged_in
	common.is_read_method
	common.is_student
	common.is_self_access
	not is_suspicious_pattern
}

# 관리자: 전체 조회 가능
allow if {
	common.is_from_gateway
	common.is_logged_in
	common.is_read_method
	common.is_admin
	not is_suspicious_pattern
}

# 교수: 자신이 담당하는 교과목의 수강 학생 성적 조회
allow if {
	common.is_from_gateway
	common.is_logged_in
	common.is_read_method
	common.is_professor
	is_course_instructor(input.user.user_id, input.course_id)
	is_enrolled_in_course(input.target_student.student_id, input.course_id)
	not is_suspicious_pattern
}
# 교수: 자신이 담당하는 교과목의 성적만 입력/수정 (기간 제한)
allow if {
	common.is_from_gateway
	common.is_logged_in
	common.is_write_method
	common.is_professor
	is_course_instructor(input.user.user_id, input.course_id)
	is_enrolled_in_course(input.target_student.student_id, input.course_id)
	is_grading_period
	not is_suspicious_pattern
}
# ──────────────────────────────────────────────────────────────
# 교수가 특정 교과목을 담당하는지 확인
is_course_instructor(professor_id, course_id) if {
	# data.courses.instructors[course_id] = ["prof001", "prof002", ...]
	data.courses.instructors[course_id][_] == professor_id
}
# 학생이 특정 교과목에 수강 중인지 확인
is_enrolled_in_course(student_id, course_id) if {
	# data.enrollments[course_id] = ["student001", "student002", ...]
	data.enrollments[course_id][_] == student_id
}
# 성적 입력 기간인지 확인
is_grading_period if {
	now := time.now_ns() / 1000000000
	date_str := time.date(now)
	
	# 겨울 학기: 2024-12-25 ~ 2025-01-07
	is_winter_grading(date_str)
}

is_grading_period if {
	now := time.now_ns() / 1000000000
	date_str := time.date(now)
	
	# 여름 학기: 2024-08-01 ~ 2024-08-14
	is_summer_grading(date_str)
}

is_winter_grading(date_str) if {
	date_str >= "2024-12-25"
	date_str <= "2025-01-07"
}

is_summer_grading(date_str) if {
	date_str >= "2024-08-01"
	date_str <= "2024-08-14"
}

# ── 이상 행동 탐지 ──────────────────────────────────────────
# 단시간 내 대량 조회 (10초 내 20회 초과)
is_suspicious_pattern if {
	input.context.recent_request_count > 20
}

# 학생이 비정상 시간대(새벽 2~5시)에 반복 조회
is_suspicious_pattern if {
	common.is_student
	input.context.hour >= 2
	input.context.hour <= 5
	input.context.recent_request_count > 5
}

# ── Critical violation (신원 신뢰 박탈 사유) ────────────────
# deny 와 달리 단순 차단이 아니라 SPIRE entry 삭제로 이어진다.

# Critical 1: 본인이 아닌 학번의 성적 조회 시도
critical_violation if {
	common.is_student
	input.query.student_id
	input.query.student_id != input.user.user_id
}

# Critical 2: 학생 권한으로 성적 변경(쓰기) 시도
critical_violation if {
	common.is_student
	not common.is_read_method
}
# Critical 3: 교수가 자신이 담당하지 않는 교과목의 성적 수정 시도
critical_violation if {
	common.is_professor
	common.is_write_method
	not is_course_instructor(input.user.user_id, input.course_id)
	input.reason := "Professor attempted to modify grades for non-assigned course"
}

# Critical 4: 교수가 자신의 교과목이 아닌데 수강하지 않는 학생의 성적 수정 시도
critical_violation if {
	common.is_professor
	common.is_write_method
	not is_enrolled_in_course(input.target_student.student_id, input.course_id)
	input.reason := "Professor attempted to modify grades for non-enrolled student"
}
# Critical 5: 성적 입력 기간 외에 성적 변경 시도
critical_violation if {
	common.is_professor
	common.is_write_method
	not is_grading_period
	input.reason := "Grade modification outside grading period"
}
