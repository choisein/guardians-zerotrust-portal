# ──────────────────────────────────────────────────────────────
# auth.rego - 로그인 서비스 인가 정책
# ──────────────────────────────────────────────────────────────
# 패키지: guardians.auth
# 적용 라우트:
#   POST /api/auth/login
#   POST /api/auth/logout
#   GET  /api/auth/session
# 특징:
#   - 로그인 전이라 user.user_id가 비어있을 수 있음 (require_session=False)
#   - 누구나 로그인 시도 가능해야 하므로 호출자가 게이트웨이인지만 확인
# ──────────────────────────────────────────────────────────────

package guardians.auth

import data.guardians.common

# 기본값: 거부 (제로트러스트 원칙)
default allow := false

# 게이트웨이를 통한 모든 인증 관련 요청 허용
# → 외부에서 auth-service를 직접 찌르는 것은 차단됨
allow if {
    common.is_from_gateway
    input.path in {
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/session",
    }
}
