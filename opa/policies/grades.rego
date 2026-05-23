# ──────────────────────────────────────────────────────────────
# grades.rego - 성적조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.grades
# 적용 라우트: GET /api/student/grades, /api/student/grades/<semester>
# 민감도: 매우 높음 (성적은 가장 민감한 데이터)
#
# 정책 요약:
#   1) 외부 요청: 게이트웨이 경유 + 로그인 + GET + 본인(또는 관리자) 조회
#   2) 내부 요청: enrollments-service 의 읽기 조회만 허용 (선수과목 검증)
#   3) 이상행동(대량/시간대/타인조회/쓰기)은 deny (entry 유지)
#   4) critical_violation (서비스 간 호출 위반) → SVID 즉시 폐지
#        - 허용 그래프 이탈 / 허용 서비스의 쓰기 / 내부 대량 호출
# ──────────────────────────────────────────────────────────────

package guardians.grades

import data.guardians.common
import rego.v1

default allow := false

default critical_violation := false

# ── 요청 출처 분류 ──────────────────────────────────────────
is_external_request if {
	input.source == "gateway"
}

is_internal_service_call if {
	input.source == "service"
	input.caller_service
}

# ── 외부 요청 (Gateway) ─────────────────────────────────────
# 학생: 본인 성적만
allow if {
	is_external_request
	common.is_logged_in
	common.is_read_method
	common.is_student
	common.is_self_access
	not is_suspicious_pattern
}

# 관리자: 전체 조회 가능
allow if {
	is_external_request
	common.is_logged_in
	common.is_read_method
	common.is_admin
	not is_suspicious_pattern
}

# ── 내부 요청 (서비스 간 호출) ──────────────────────────────
# Enrollment Service: 선수과목/수강 확인을 위해 성적 조회 (읽기만)
allow if {
	is_internal_service_call
	input.caller_service == "enrollments-service"
	common.is_read_method
}

# ── 이상 행동 탐지 (deny, entry 유지) ───────────────────────
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

# 관리자가 특정 학생의 데이터를 반복 조회 (감시 행위)
is_suspicious_pattern if {
	common.is_admin
	input.target_student.student_id
	input.context.same_student_count > 20
}

# 관리자가 전체 학생 데이터 일괄 다운로드 시도
is_suspicious_pattern if {
	common.is_admin
	input.request.bulk_export == true
}

# (구) 사용자 위반 → 이상행동으로 강등: 본인 외 학번 조회 시도
is_suspicious_pattern if {
	common.is_student
	input.query.student_id
	input.query.student_id != input.user.user_id
}

# (구) 사용자 위반 → 이상행동으로 강등: 학생 권한 쓰기 시도
is_suspicious_pattern if {
	common.is_student
	not common.is_read_method
}

# ── 서비스 간 호출 위반 (critical_violation → SVID 폐지) ─────
# 횡적 이동 차단. 허가된 호출 그래프를 벗어난 서비스 신원을 폐지한다.
allowed_internal_callers := {"enrollments-service"}

# [시나리오 A·B] 호출 그래프 이탈: 허가되지 않은 서비스의 내부 호출
critical_violation if {
	is_internal_service_call
	not input.caller_service in allowed_internal_callers
}

# [시나리오 D] 메서드 초과: 허가된 서비스라도 읽기 외(쓰기) 시도
critical_violation if {
	is_internal_service_call
	input.caller_service in allowed_internal_callers
	not common.is_read_method
}

# [시나리오 E] 대량 추출: 내부 서비스의 단시간 대량 호출 (임계값 조정 가능)
critical_violation if {
	is_internal_service_call
	input.context.recent_request_count > 20
}
