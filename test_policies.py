"""
정책 시나리오 테스트 - 22개 케이스로 정책 로직을 검증
실행: python3 test_policies.py
"""
import sys
from policy_simulator import EVALUATORS


# ─── 기본 input 빌더 ─────────────────────────────────────
def make_input(
    caller="spiffe://guardians.local/service/gateway",
    user_id="20230001",
    role="student",
    method="GET",
    path="/api/student/profile",
    query=None,
    hour=14,
    recent_count=1,
):
    return {
        "caller_spiffe_id": caller,
        "service_spiffe_id": "spiffe://guardians.local/service/profile",
        "user": {"user_id": user_id, "role": role},
        "method": method,
        "path": path,
        "query": query or {},
        "context": {
            "hour": hour,
            "recent_request_count": recent_count,
            "timestamp": "2026-04-27T14:00:00",
            "client_ip": "192.168.1.10",
        },
    }


# ─── 테스트 케이스 ─────────────────────────────────────────
# (설명, 정책패키지, input, 기대결과)
TESTS = [
    # 1. 정상 학생 시나리오
    ("학생이 본인 학적 조회", "guardians/profile",
     make_input(path="/api/student/profile"), True),
    ("학생이 본인 성적 조회", "guardians/grades",
     make_input(path="/api/student/grades"), True),
    ("학생이 본인 수강내역 조회", "guardians/enrollments",
     make_input(path="/api/student/enrollments"), True),
    ("학생이 본인 등록정보 조회", "guardians/registrations",
     make_input(path="/api/student/registrations"), True),

    # 2. 권한 위반 - 차단되어야 함
    ("학생이 다른 학생 학적 조회 시도", "guardians/profile",
     make_input(query={"student_id": "20230002"}), False),
    ("학생이 다른 학생 성적 조회 시도", "guardians/grades",
     make_input(path="/api/student/grades", query={"student_id": "20230099"}), False),

    # 3. 관리자 시나리오
    ("관리자가 학생 학적 조회", "guardians/profile",
     make_input(role="admin", user_id="admin1", query={"student_id": "20230001"}), True),
    ("관리자가 학생 성적 조회", "guardians/grades",
     make_input(role="admin", user_id="admin1", path="/api/student/grades",
                query={"student_id": "20230001"}), True),

    # 4. 인증 실패 - 차단되어야 함
    ("로그인 안 한 사용자", "guardians/profile",
     make_input(user_id="", role=None), False),
    ("게이트웨이 우회 직접 호출", "guardians/grades",
     make_input(caller="spiffe://attacker/service/x", path="/api/student/grades"), False),
    ("외부 IP에서 직접 호출", "guardians/profile",
     make_input(caller="external-attacker"), False),

    # 5. 메서드 위반
    ("POST로 학적 변경 시도", "guardians/profile",
     make_input(method="POST"), False),
    ("DELETE 시도", "guardians/grades",
     make_input(path="/api/student/grades", method="DELETE"), False),

    # 6. 이상행동 탐지 (성적조회)
    ("성적: 10초 내 21회 조회 (대량조회)", "guardians/grades",
     make_input(path="/api/student/grades", recent_count=21), False),
    ("성적: 학생이 새벽 3시에 6회 조회", "guardians/grades",
     make_input(path="/api/student/grades", hour=3, recent_count=6), False),
    ("성적: 학생이 새벽 3시에 1회 조회 (정상)", "guardians/grades",
     make_input(path="/api/student/grades", hour=3, recent_count=1), True),
    ("성적: 관리자는 새벽이어도 통과", "guardians/grades",
     make_input(role="admin", user_id="admin1", path="/api/student/grades",
                hour=3, recent_count=10, query={"student_id": "20230001"}), True),

    # 7. 등록금 이상행동
    ("등록금: 10초 내 25회 조회", "guardians/registrations",
     make_input(path="/api/student/registrations", recent_count=25), False),
    ("등록금: 정상 1회 조회", "guardians/registrations",
     make_input(path="/api/student/registrations", recent_count=2), True),

    # 8. 로그인 정책
    ("로그인 요청 (세션 없어도 통과)", "guardians/auth",
     make_input(user_id=None, role=None, method="POST",
                path="/api/auth/login"), True),
    ("외부에서 직접 로그인 시도", "guardians/auth",
     make_input(caller="attacker", user_id=None, role=None,
                method="POST", path="/api/auth/login"), False),
    ("이상한 경로로 인증 우회 시도", "guardians/auth",
     make_input(user_id=None, role=None, method="POST",
                path="/api/auth/admin-bypass"), False),
]


def run_tests():
    print("=" * 70)
    print("OPA 정책 시나리오 테스트")
    print("=" * 70)
    passed = 0
    failed = 0
    for i, (desc, pkg, inp, expected) in enumerate(TESTS, 1):
        evaluator = EVALUATORS[pkg]
        actual = evaluator(inp)
        status = "✓ PASS" if actual == expected else "✗ FAIL"
        result_str = "허용" if actual else "거부"
        expected_str = "허용" if expected else "거부"
        print(f"  {status}  [{i:2d}] {desc}")
        print(f"          → {pkg}: {result_str} (기대: {expected_str})")
        if actual == expected:
            passed += 1
        else:
            failed += 1
            print(f"          ⚠ 입력: {inp}")
    print("=" * 70)
    print(f"총 {len(TESTS)}개 중 통과: {passed}, 실패: {failed}")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
