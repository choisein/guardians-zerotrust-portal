#!/usr/bin/env python3
"""
attack_demo.py - OPA 정책이 공격을 어떻게 막는지 보여주는 데모
실행 전제: docker compose up 으로 게이트웨이가 띄워져 있어야 함
실행: python3 attack_demo.py
"""
import requests
import time

GATEWAY = "http://localhost:5000"


def banner(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


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


# ─────────────────────────────────────────────
# 시나리오 1: 정상 학생 접근 (통과해야 함)
# ─────────────────────────────────────────────
banner("시나리오 1: 정상 학생이 본인 정보 조회")
s = login("20230001", "password")
show_response("학적 조회", s.get(f"{GATEWAY}/api/student/profile"))
show_response("성적 조회", s.get(f"{GATEWAY}/api/student/grades"))

# ─────────────────────────────────────────────
# 시나리오 2: 단순 deny - 대량 조회 (entry 유지, 접근만 차단)
# ─────────────────────────────────────────────
banner("시나리오 2: 대량 조회 공격 → deny (entry는 유지)")
print("  25회 연속 요청 시작...")
allowed, denied = 0, 0
for i in range(25):
    r = s.get(f"{GATEWAY}/api/student/grades")
    if r.status_code == 200:
        allowed += 1
    elif r.status_code == 403:
        denied += 1
print(f"  ✓ 결과: 허용 {allowed}회, 차단 {denied}회")
print("  → 21회 이상부터 OPA 가 deny 로 자동 차단 (entry/SVID 는 유지됨)")

print()
print("  10초 대기 (카운터 리셋 중)...")
time.sleep(11)

# 카운터 리셋 후 정상 접근 가능 확인 (entry 가 유지됐음을 입증)
show_response("리셋 후 정상 조회 가능 여부", s.get(f"{GATEWAY}/api/student/profile"))

# ─────────────────────────────────────────────
# 시나리오 3: 게이트웨이 우회 직접 호출 (차단)
# ─────────────────────────────────────────────
banner("시나리오 3: 게이트웨이 우회 → grades-service 직접 호출")
try:
    r = requests.get("http://localhost:5003/api/student/grades", timeout=3)
    show_response("직접 호출 결과", r)
except requests.RequestException as e:
    print(f"  → 연결 실패 (서비스가 외부 노출 안 됨): {e}")

# ─────────────────────────────────────────────
# 시나리오 4: critical_violation - 타 학번 성적 조회 시도
#   → entry 삭제 + blocklist 등록 (SVID 즉시 무효화)
# ─────────────────────────────────────────────
banner("시나리오 4: 타 학번 성적 조회 → critical_violation (entry 삭제)")
victim = login("20230001", "password")  # 새 세션 (이전 시나리오 영향 차단)
print("  1) 사전 확인: 본인 성적은 정상 조회됨")
show_response("본인 성적", victim.get(f"{GATEWAY}/api/student/grades"))

print()
print("  2) 공격: 타 학번 성적 조회 시도")
show_response("타 학번 성적 조회",
              victim.get(f"{GATEWAY}/api/student/grades?student_id=20230099"))
print("     → 응답에 reason=critical_violation 이 보여야 함")
print("     → 게이트웨이 로그에 [REVOKE] / [BLOCKLIST] 메시지 출력")

print()
print("  3) 사후 확인: 동일 세션의 후속 요청도 즉시 무효화되어야 함")
#   - 게이트웨이의 caller_spiffe_id 가 blocklist 에 올라갔으므로
#     이후 게이트웨이 → 마이크로서비스 호출의 SVID 검증이 거부됨
show_response("정상 본인 조회 재시도",
              victim.get(f"{GATEWAY}/api/student/profile"))
print("     → 401/403 이 나와야 하며, 게이트웨이/서비스 로그에")
print("       \"[BLOCKLIST] 폐기된 SPIFFE ID 의 ... 거부\" 가 보여야 함")

# ─────────────────────────────────────────────
# 시나리오 5: critical_violation - 학생이 성적 수정 시도 (write)
# ─────────────────────────────────────────────
banner("시나리오 5: 학생이 성적 변경(POST) 시도 → critical_violation")
attacker = login("20230002", "password")
show_response("성적 수정 시도",
              attacker.post(f"{GATEWAY}/api/student/grades",
                            json={"course": "CS101", "score": 100}))
print("     → reason=critical_violation, entry 삭제, blocklist 등록 확인")

# ─────────────────────────────────────────────
# 시나리오 6: 관리자 정상 접근
# ─────────────────────────────────────────────
banner("시나리오 6: 관리자가 학생 정보 조회 (통과)")
admin = login("admin1", "admin")
show_response("관리자 학적 조회",
              admin.get(f"{GATEWAY}/api/student/profile?student_id=20230001"))

print()
print("=" * 60)
print("  데모 종료")
print("=" * 60)
print()
print("[복구] entry 가 삭제된 학생을 다시 사용하려면 SPIRE entry 재등록 필요:")
print("  docker compose exec spire-server sh /spire/scripts/register-workloads.sh")
print("  docker compose restart gateway   # blocklist (in-memory) 초기화")
