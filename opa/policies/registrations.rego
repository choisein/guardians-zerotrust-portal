# ──────────────────────────────────────────────────────────────
# registrations.rego - 등록금납부조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.registrations
# 적용 라우트:
#   GET /api/student/registrations
# 민감도: 높음 (등록금/금융 정보)
#
# 정책 요약:
#   1) 게이트웨이를 통한 요청만 허용
#   2) 로그인된 사용자만 허용
#   3) GET 요청만 허용
#   4) 학생: 본인 등록정보만, 관리자: 전체 조회
#   5) 추가 보호: 대량 조회 차단
# ──────────────────────────────────────────────────────────────

package guardians.registrations

import data.guardians.common

default allow := false

# 학생: 본인 등록 정보만
allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_student
    common.is_self_access
    not is_suspicious_pattern
}

# 관리자: 전체 조회
allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_admin
    not is_suspicious_pattern
}

# 대량 조회 탐지
is_suspicious_pattern if {
    input.context.recent_request_count > 20
}
