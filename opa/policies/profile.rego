# ──────────────────────────────────────────────────────────────
# profile.rego - 학적조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.profile
# 적용 라우트:
#   GET /api/student/profile
# 민감도: 높음 (학적 정보)
#
# 정책 요약:
#   1) 게이트웨이를 통한 요청만 허용 (서비스 간 mTLS 인증)
#   2) 로그인된 사용자만 허용
#   3) GET 요청만 허용
#   4) 학생: 본인 학적만 조회 가능
#      관리자: 모든 학생 학적 조회 가능 (단, student_id 파라미터 필수)
# ──────────────────────────────────────────────────────────────

package guardians.profile

import data.guardians.common

default allow := false

# 학생 케이스: 본인의 학적 정보만 조회
allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_student
    common.is_self_access
}

# 관리자 케이스: 모든 학생 학적 조회 가능
# (관리자는 student_id를 명시해야 하므로 라우트 코드에서 검증됨)
allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_admin
}
