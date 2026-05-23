# ──────────────────────────────────────────────────────────────
# profile.rego - 학적조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.profile
# 적용 라우트: GET /api/student/profile
# 민감도: 높음 (학적 정보)
#
# 정책 요약:
#   1) 외부 요청: 게이트웨이 경유 + 로그인 + GET + 본인(또는 관리자) 조회
#   2) 내부 요청: enrollments-service 의 읽기 조회만 허용 (수강 자격 확인)
#   3) 이상행동(대량/시간대/타인조회)은 deny (entry 유지)
#   4) critical_violation (서비스 간 호출 위반) → SVID 즉시 폐지
# ──────────────────────────────────────────────────────────────

package guardians.profile

import data.guardians.common
import rego.v1

default allow := false

default critical_violation := false

# ── 외부 요청 (Gateway) ─────────────────────────────────────
# 학생: 본인의 학적 정보만 조회
allow if {
	common.is_from_gateway
	common.is_logged_in
	common.is_read_method
	common.is_student
	common.is_self_access
	not is_suspicious_pattern
}

# 관리자: 모든 학생 학적 조회 가능
allow if {
	common.is_from_gateway
	common.is_logged_in
	common.is_read_method
	common.is_admin
	not is_suspicious_pattern
}

# ── 내부 요청 (서비스 간 호출) ──────────────────────────────
# Enrollment Service: 수강 자격(학년·전공) 확인을 위해 학적 조회 (읽기만)
allow if {
	common.is_internal_service_call
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

# (구) 사용자 위반 → 이상행동으로 강등: 본인 외 학번 학적 조회 시도
is_suspicious_pattern if {
	common.is_student
	input.query.student_id
	input.query.student_id != input.user.user_id
}

# ── 서비스 간 호출 위반 (critical_violation → SVID 폐지) ─────
allowed_internal_callers := {"enrollments-service"}

# [시나리오 A·B] 호출 그래프 이탈: 허가되지 않은 서비스의 내부 호출
critical_violation if {
	common.is_internal_service_call
	not input.caller_service in allowed_internal_callers
}

# [시나리오 D] 메서드 초과: 허가된 서비스라도 읽기 외(쓰기) 시도
critical_violation if {
	common.is_internal_service_call
	input.caller_service in allowed_internal_callers
	not common.is_read_method
}

# [시나리오 E] 대량 추출: 내부 서비스의 단시간 대량 호출 (임계값 조정 가능)
critical_violation if {
	common.is_internal_service_call
	input.context.recent_request_count > 20
}
