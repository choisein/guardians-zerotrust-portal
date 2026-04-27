# ──────────────────────────────────────────────────────────────
# common.rego - 모든 서비스 정책에서 공유하는 헬퍼 함수
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.common
# 역할:
#   1) 호출자가 게이트웨이인지 검증 (서비스 간 통신 인증)
#   2) 사용자 역할 확인 헬퍼
#   3) HTTP 메서드 화이트리스트 체크
# ──────────────────────────────────────────────────────────────

package guardians.common

# 신뢰할 수 있는 호출자 (게이트웨이만 각 서비스를 호출할 수 있음)
trusted_callers := {
    "spiffe://guardians.local/service/gateway",
}

# 호출자 SPIFFE ID가 게이트웨이인지 확인
# → 외부에서 마이크로서비스를 직접 호출하는 것을 차단 (서비스 간 mTLS 인증 강제)
is_from_gateway if {
    input.caller_spiffe_id in trusted_callers
}

# 개발 모드에서는 dev-local 호출도 허용 (SVID 없이 테스트 가능하도록)
# 운영에서는 REQUIRE_SVID=true로 막혀있음
is_from_gateway if {
    input.caller_spiffe_id == "dev-local"
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

# 메서드가 허용된 메서드인지 (조회 위주)
is_read_method if {
    input.method in {"GET", "HEAD"}
}

# 학생이 조회하는 student_id가 본인의 것인지 확인
# (query 파라미터에 student_id가 없으면 본인 데이터로 간주하여 통과)
is_self_access if {
    not input.query.student_id
}

is_self_access if {
    input.query.student_id == input.user.user_id
}
