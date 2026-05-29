# ──────────────────────────────────────────────────────────────
# enrollments.rego - 수강내역조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.enrollments
# 적용 라우트: GET /api/student/enrollments
# 민감도: 중간 (수강 내역)
#
# 정책 요약:
#   1) 외부 요청: 게이트웨이 경유 + 로그인 + GET + 본인(또는 관리자) 조회
#   2) 내부 요청: registrations-service 의 읽기 조회만 허용 (등록금 산정)
#   3) critical_violation (서비스 간 호출 위반) → SVID 즉시 폐지
# ──────────────────────────────────────────────────────────────

package guardians.enrollments

import data.guardians.common
import rego.v1

default allow := false

default critical_violation := false

# 학생: 본인의 수강내역만 조회
allow if {
	common.is_logged_in
	common.is_read_method
	common.is_student
	common.is_self_access
}

# 관리자: 모든 학생의 수강내역 조회
allow if {
	common.is_logged_in
	common.is_read_method
	common.is_admin
}

# ── 서비스 간 호출 위반 (critical_violation → SVID 폐지) ─────
allowed_internal_callers := {"registrations-service"}

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
