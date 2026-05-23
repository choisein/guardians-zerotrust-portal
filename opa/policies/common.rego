# ──────────────────────────────────────────────────────────────
# common.rego - 모든 서비스 정책에서 공유하는 헬퍼 함수
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.common
# 역할:
#   1) 호출자가 게이트웨이인지 검증 (서비스 간 통신 인증)
#   2) 요청 출처(외부/내부) 구분
#   3) 사용자 역할 확인 / HTTP 메서드 화이트리스트 체크
# ──────────────────────────────────────────────────────────────

package guardians.common

# OPA 0.66+ 에서 `if`, `in`, `contains`, `every` 키워드 사용 활성화.
import rego.v1

# 신뢰할 수 있는 호출자 (게이트웨이만 각 서비스를 외부 진입점으로 호출)
trusted_callers := {"spiffe://guardians.local/service/gateway"}

# 호출자 SPIFFE ID가 게이트웨이인지 확인
is_from_gateway if {
	input.caller_spiffe_id in trusted_callers
}

# 개발 모드에서는 dev-local 호출도 허용 (운영에서는 REQUIRE_SVID=true로 막힘)
is_from_gateway if {
	input.caller_spiffe_id == "dev-local"
}

# ──────────────────────────────────────────────────────────────
# 요청 출처 구분 (미들웨어가 caller_spiffe_id 에서 파생해 전달)
#   - source == "gateway" : 외부 진입점(게이트웨이) 경유 요청 / 개발모드
#   - source == "service" : 서비스 간 내부 호출 (caller_service 동반)
# ──────────────────────────────────────────────────────────────
is_external_request if {
	input.source == "gateway"
}

is_internal_service_call if {
	input.source == "service"
	input.caller_service
}

# 사용자가 학생 역할인지
is_student if {
	input.user.role == "student"
}

# 사용자가 관리자 역할인지
is_admin if {
	input.user.role == "admin"
}

# 로그인된 사용자인지 (세션이 있는지)
is_logged_in if {
	input.user.user_id
	input.user.user_id != null
	input.user.user_id != ""
}

# 메서드가 허용된 조회 메서드인지
is_read_method if {
	input.method in {"GET", "HEAD"}
}

# 학생이 조회하는 student_id가 본인의 것인지 확인
is_self_access if {
	not input.query.student_id
}

is_self_access if {
	input.query.student_id == input.user.user_id
}
