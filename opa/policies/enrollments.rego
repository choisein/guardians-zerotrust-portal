# ──────────────────────────────────────────────────────────────
# enrollments.rego - 수강내역조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.enrollments
# 적용 라우트:
#   GET /api/student/enrollments
# 민감도: 중간 (수강 내역)
#
# 정책 요약:
#   1) 게이트웨이를 통한 요청만 허용
#   2) 로그인된 사용자만 허용
#   3) GET 요청만 허용
#   4) 학생: 본인 수강내역만, 관리자: 전체 조회
# ──────────────────────────────────────────────────────────────

package guardians.enrollments

import rego.v1
import data.guardians.common

default allow := false

# ═══════════════════════════════════════════════════════════════
# 외부/내부 요청 판단
# ═══════════════════════════════════════════════════════════════

# 외부 클라이언트 요청 (Gateway를 통함)
is_external_request if {
	input.source == "gateway"
}

# 내부 서비스 호출 (mTLS/SPIRE를 통함)
is_internal_service_call if {
	input.source == "service"
	input.caller_service  # "grades-service", "audit-service" 등
}
# ═══════════════════════════════════════════════════════════════
# 외부 요청 인가 규칙
# ═══════════════════════════════════════════════════════════════

# 학생: 본인의 수강내역만 조회
allow if {
	is_external_request
	common.is_logged_in
	common.is_read_method
	common.is_student
	common.is_self_access
}

# 관리자: 모든 학생의 수강내역 조회
allow if {
	is_external_request
	common.is_logged_in
	common.is_read_method
	common.is_admin
}
# ═══════════════════════════════════════════════════════════════
# 내부 요청 인가 규칙
# ═══════════════════════════════════════════════════════════════

# Grades Service: 학생의 수강내역 확인 (읽기만)
allow if {
	is_internal_service_call
	input.caller_service == "grades-service"
	common.is_read_method
}

# Audit Service: 학생의 수강내역 감시 (읽기 + 로깅)
allow if {
	is_internal_service_call
	input.caller_service == "audit-service"
	(common.is_read_method | common.is_write_method)
}
