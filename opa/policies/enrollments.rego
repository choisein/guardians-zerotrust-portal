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

import data.guardians.common

default allow := false

allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_student
    common.is_self_access
}

allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_admin
}
