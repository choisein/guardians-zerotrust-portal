# ──────────────────────────────────────────────────────────────
# grades.rego - 성적조회 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.grades
# 적용 라우트:
#   GET /api/student/grades
#   GET /api/student/grades/<semester>
# 민감도: 매우 높음 (성적은 가장 민감한 데이터)
#
# 정책 요약 (profile보다 엄격):
#   1) 게이트웨이를 통한 요청만 허용
#   2) 로그인된 사용자만 허용
#   3) GET 요청만 허용
#   4) 학생: 본인 성적만 조회 가능
#   5) 관리자: 모든 성적 조회 가능
#   6) 추가 보호: 비정상적 패턴 (대량 조회) 차단
# ──────────────────────────────────────────────────────────────

package guardians.grades

import data.guardians.common

default allow := false

# 학생 케이스: 본인 성적만
allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_student
    common.is_self_access
    not is_suspicious_pattern
}

# 관리자 케이스: 전체 조회 가능
allow if {
    common.is_from_gateway
    common.is_logged_in
    common.is_read_method
    common.is_admin
    not is_suspicious_pattern
}

# ── 이상 행동 탐지 ──────────────────────────────────────────
# 미들웨어가 input.context에 다음 필드를 채워 보내면 활성화됨:
#   recent_request_count: 최근 10초 내 동일 사용자 요청 수
#   hour: 현재 시각(0~23)

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
