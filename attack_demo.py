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
        print(f"        → {msg}")
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
# 시나리오 2: 권한 위반 - 학생이 다른 학생 정보 조회 시도
# ─────────────────────────────────────────────
banner("시나리오 2: 학생이 다른 학생 성적 조회 시도 (OPA 차단)")
show_response("타인 성적 조회 시도",
              s.get(f"{GATEWAY}/api/student/grades?student_id=20230099"))

# ─────────────────────────────────────────────
# 시나리오 3: 대량 조회 공격 (이상행동 탐지)
# ─────────────────────────────────────────────
banner("시나리오 3: 대량 조회 공격 (10초 내 25회)")
print("  25회 연속 요청 시작...")
allowed = 0
denied = 0
for i in range(25):
    r = s.get(f"{GATEWAY}/api/student/grades")
    if r.status_code == 200:
        allowed += 1
    elif r.status_code == 403:
        denied += 1
print(f"  ✓ 결과: 허용 {allowed}회, 차단 {denied}회")
print(f"  → 21회 이상부터 OPA가 자동 차단해야 함")

# 카운터 리셋을 위해 잠시 대기
print()
print("  10초 대기 (카운터 리셋 중)...")
time.sleep(11)

# ─────────────────────────────────────────────
# 시나리오 4: 게이트웨이 우회 직접 호출 (차단)
# ─────────────────────────────────────────────
banner("시나리오 4: 게이트웨이 우회 → grades-service 직접 호출")
try:
    # SVID 없이 직접 호출 시도
    r = requests.get("http://localhost:5003/api/student/grades", timeout=3)
    show_response("직접 호출 결과", r)
except requests.RequestException as e:
    print(f"  → 연결 실패 (서비스가 외부 노출 안 됨): {e}")

# ─────────────────────────────────────────────
# 시나리오 5: 관리자 정상 접근
# ─────────────────────────────────────────────
banner("시나리오 5: 관리자가 학생 정보 조회 (통과)")
admin = login("admin1", "admin")
show_response("관리자 학적 조회",
              admin.get(f"{GATEWAY}/api/student/profile?student_id=20230001"))

print()
print("=" * 60)
print("  데모 종료")
print("=" * 60)
