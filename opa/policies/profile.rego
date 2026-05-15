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
#      관리자: 모든 학생 학적 조회 가능
#   5) 추가 보호: 비정상적 패턴 (대량 조회) 차단
#   6) critical_violation (신뢰 박탈 사유): 본인 외 학번 조회 시도
#      → 미들웨어가 SPIRE entry 를 즉시 삭제
# ──────────────────────────────────────────────────────────────

package guardians.profile

import rego.v1
import data.guardians.common

default allow := false
default critical_violation := false

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

# ── 이상 행동 탐지 ──────────────────────────────────────────
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

# ── Critical violation (신원 신뢰 박탈 사유) ────────────────
# deny 와 달리 단순 차단이 아니라 SPIRE entry 삭제로 이어진다.
# "본인이 아닌 학번의 학적을 조회하려는 시도" 자체를 악의로 간주한다.
critical_violation if {
	common.is_student
	input.query.student_id
	input.query.student_id != input.user.user_id
}
