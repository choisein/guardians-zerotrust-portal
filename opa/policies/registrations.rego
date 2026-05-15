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
#   6) critical_violation (신뢰 박탈 사유):
#        - 본인 외 학번의 등록 정보 조회 시도
#        - 학생 권한으로 등록금 정보 변경(쓰기) 시도
#      → 미들웨어가 SPIRE entry 를 즉시 삭제
# ──────────────────────────────────────────────────────────────

package guardians.registrations

import rego.v1
import data.guardians.common

default allow := false
default critical_violation := false

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

# ── Critical violation (신원 신뢰 박탈 사유) ────────────────
# deny 와 달리 단순 차단이 아니라 SPIRE entry 삭제로 이어진다.

# Critical 1: 본인이 아닌 학번의 등록 정보 조회 시도
critical_violation if {
	common.is_student
	input.query.student_id
	input.query.student_id != input.user.user_id
}

# Critical 2: 학생 권한으로 등록금 정보 변경(쓰기) 시도
critical_violation if {
	common.is_student
	not common.is_read_method
}
