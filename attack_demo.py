#!/usr/bin/env python3
"""
attack_demo.py - OPA 정책이 공격을 어떻게 막는지 보여주는 데모 (시나리오 S1~S10)

실행 전제: docker compose up -d --build 로 전체 스택이 떠 있어야 함
실행:      python3 attack_demo.py

시나리오 문서(공격테스트_시나리오_설명.md)의 S1~S10 과 1:1 대응한다.
  [계층 1 / 사용자 계층 → allow·deny]
    S1 정상 본인 조회        S2 미인증 접근        S3 타 학번 조회
    S4 학생 쓰기 시도        S5 대량 조회          S6 관리자 전체 조회
    S7 게이트웨이 우회
  [계층 2 / 워크로드 계층 → allow·critical_violation(SVID 폐지+failover)]
    S8 허용된 내부 호출      S9 profile→grades 이탈(★)   S10 registrations→grades 이탈
"""
import requests
import time

GATEWAY = "http://localhost:5000"
REVOCATION_STORE = "http://localhost:6000"


# ─────────────────────────────────────────────
# 출력 헬퍼
# ─────────────────────────────────────────────
def banner(title):
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)


def login(user_id, password):
    s = requests.Session()
    r = s.post(f"{GATEWAY}/api/auth/login",
               json={"user_id": user_id, "password": password})
    if r.status_code == 200:
        print(f"  ✓ {user_id} 로그인 성공")
    else:
        print(f"  ✗ 로그인 실패: {r.status_code} {r.text}")
    return s


def show_response(label, resp):
    print(f"  [{resp.status_code}] {label}")
    try:
        body = resp.json()
        msg = body.get("error") or body.get("message") or str(body)[:100]
        reason = body.get("reason")
        suffix = f" (reason={reason})" if reason else ""
        print(f"        → {msg}{suffix}")
    except Exception:
        print(f"        → {resp.text[:100]}")


def reset_revocations():
    """데모 반복 가능하도록 폐지 기록 초기화."""
    try:
        requests.post(f"{REVOCATION_STORE}/reset", timeout=2)
        print("  (revocation-store 초기화 완료)")
    except requests.RequestException:
        print("  (revocation-store 초기화 생략 — 미기동?)")


# ══════════════════════════════════════════════════════════════
#  계층 1 — 사용자 계층 (allow / deny, SVID 폐지 없음)
# ══════════════════════════════════════════════════════════════

# ── S1. 정상 본인 조회 (allow) — 기준선 ───────────────────────
banner("S1. 정상 학생이 본인 정보 조회 (기대: 전부 200 allow)")
s = login("user_202300001", "test1234")
show_response("학적 조회", s.get(f"{GATEWAY}/api/student/profile"))
show_response("성적 조회", s.get(f"{GATEWAY}/api/student/grades"))
show_response("수강내역 조회", s.get(f"{GATEWAY}/api/student/enrollments"))
show_response("등록정보 조회", s.get(f"{GATEWAY}/api/student/registrations"))

# ── S2. 미인증 접근 (deny, 401) ──────────────────────────────
banner("S2. 로그인 안 한 세션으로 접근 (기대: 401 deny)")
anon = requests.Session()  # 로그인하지 않은 빈 세션
show_response("미인증 학적 조회", anon.get(f"{GATEWAY}/api/student/profile"))

# ── S3. 타 학번 조회 (deny, entry 유지) ──────────────────────
banner("S3. 타 학번 성적 조회 시도 (기대: 403 deny, entry 유지)")
show_response("본인 성적(정상)", s.get(f"{GATEWAY}/api/student/grades"))
show_response("타 학번 성적(공격)",
              s.get(f"{GATEWAY}/api/student/grades?student_id=user_201800002"))
print("  → 공격 직후에도 본인 조회는 다시 통과해야 함 (deny 는 신원 유지)")
show_response("공격 직후 본인 성적 재조회", s.get(f"{GATEWAY}/api/student/grades"))

# ── S4. 학생 쓰기 시도 (deny) ────────────────────────────────
banner("S4. 학생이 성적 변경(POST) 시도 (기대: 403 deny)")
attacker = login("user_202300001", "test1234")
show_response("정상 본인 성적 조회", attacker.get(f"{GATEWAY}/api/student/grades"))
show_response("성적 수정 시도(공격)",
              attacker.post(f"{GATEWAY}/api/student/grades",
                            json={"course": "CS101", "score": 100}))

# ── S5. 단시간 대량 조회 (deny, 이상행동, entry 유지) ─────────
banner("S5. 10초 내 25회 대량 조회 (기대: 21회째부터 403, 이후 회복)")
# 직전 시나리오의 요청이 10초 슬라이딩 윈도우에 남아 있어 카운터가 누적되므로 리셋 대기
print("  카운터 리셋 대기 11초 ...")
time.sleep(11)
print("  25회 연속 요청 시작...")
allowed, denied = 0, 0
for _ in range(25):
    r = s.get(f"{GATEWAY}/api/student/grades")
    if r.status_code == 200:
        allowed += 1
    elif r.status_code == 403:
        denied += 1
print(f"  ✓ 결과: 허용 {allowed}회, 차단 {denied}회")
print("  → recent_request_count > 20 부터 OPA 가 deny 로 자동 차단 (entry 유지)")
print()
print("  10초 대기 (카운터 리셋 중)...")
time.sleep(11)
show_response("리셋 후 정상 조회 가능 여부", s.get(f"{GATEWAY}/api/student/profile"))

# ── S6. 관리자 정상 전체 조회 (allow) ────────────────────────
banner("S6. 관리자 전체 조회 vs 학생 타인 조회 (기대: admin 200 / student 403)")
admin = login("admin_001", "test1234")
show_response("관리자 → 학생 학적 조회",
              admin.get(f"{GATEWAY}/api/student/profile?student_id=202300001"))
show_response("학생 → 타 학생 학적 조회(대조)",
              s.get(f"{GATEWAY}/api/student/profile?student_id=20230002"))

# ── S7. 게이트웨이 우회 직접 호출 (deny / 차단) ──────────────
banner("S7. 게이트웨이 우회 → grades-service 직접 호출 (기대: 401 또는 연결거부)")
try:
    r = requests.get("http://localhost:5003/api/student/grades", timeout=3)
    show_response("직접 호출 결과", r)
except requests.RequestException as e:
    print(f"  → 연결 실패 (서비스가 외부 노출 안 됨): {e}")


# ══════════════════════════════════════════════════════════════
#  계층 2 — 워크로드 계층 (allow / critical_violation → SVID 폐지 + failover)
#  ※ 반복 실행을 위해 폐지 기록을 먼저 초기화
# ══════════════════════════════════════════════════════════════
banner("계층 2 시작 전: 폐지 기록 초기화")
reset_revocations()

# ── S8. 허용된 내부 호출 (allow) — 계층 2 기준선 ─────────────
banner("S8. 허용된 서비스 간 내부 호출 (기대: 전부 200 allow)")
internal = login("user_202300001", "test1234")
show_response("enrollments → grades",
              internal.get(f"{GATEWAY}/api/student/enrollments/internal/grades"))
show_response("enrollments → profile",
              internal.get(f"{GATEWAY}/api/student/enrollments/internal/profile"))
show_response("registrations → enrollments",
              internal.get(f"{GATEWAY}/api/student/registrations/internal/enrollments"))

# ── S9. profile → grades 그래프 이탈 → critical (★) ──────────
banner("S9. ★ profile → grades 횡적 이동 (기대: 403 critical → profile SVID 폐지 → failover)")
print("  1) 공격: 호출 그래프를 벗어난 내부 호출 (profile → grades)")
show_response("profile → grades (그래프 이탈)",
              internal.get(f"{GATEWAY}/api/student/profile/internal/grades"))
print("     → reason=critical_violation 확인")
print("     → grades 서비스 로그: [CRITICAL]/[REVOKE]/[BLOCKLIST]")
print("     → revocation-store 로 [FAILOVER] 차단 신호, profile.revoked 생성")
print()
print("  2) 사후 확인: 이후 /profile 요청은 게이트웨이가 profile-replica 로 우회")
time.sleep(1)
show_response("폐지 후 학적 조회 (replica 가 처리)",
              internal.get(f"{GATEWAY}/api/student/profile"))
print("     → 사용자에게는 여전히 200 (가용성 유지). 게이트웨이 로그: [FAILOVER] profile 폐지됨 →")

# ── S10. registrations → grades 그래프 이탈 → critical ───────
banner("S10. registrations → grades 횡적 이동 (기대: 403 critical → registrations SVID 폐지 → failover)")
print("  1) 공격: 호출 그래프를 벗어난 내부 호출 (registrations → grades)")
show_response("registrations → grades (그래프 이탈)",
              internal.get(f"{GATEWAY}/api/student/registrations/internal/grades"))
print("     → reason=critical_violation, registrations SVID 폐지")
print()
print("  2) 사후 확인: 이후 /registrations 요청은 registrations-replica 로 우회")
time.sleep(1)
show_response("폐지 후 등록정보 조회 (replica 가 처리)",
              internal.get(f"{GATEWAY}/api/student/registrations"))


# ══════════════════════════════════════════════════════════════
print()
print("=" * 64)
print("  데모 종료 (S1~S10)")
print("=" * 64)
print()
print("[복구] 폐지된 서비스(profile, registrations)를 원복하려면:")
print("  curl -X POST http://localhost:6000/reset      # 폐지 기록 삭제")
print("  docker compose exec spire-server sh /spire/scripts/register-workloads.sh")
print("  docker compose restart gateway profile-service registrations-service")