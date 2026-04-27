"""
정책 시뮬레이터 - Rego 정책 로직을 Python으로 동일하게 구현하여
                  test_policies.py가 검증할 수 있도록 함
"""

TRUSTED_CALLERS = {
    "spiffe://guardians.local/service/gateway",
    "dev-local",
}


def _is_from_gateway(inp):
    return inp.get("caller_spiffe_id") in TRUSTED_CALLERS


def _is_logged_in(inp):
    uid = inp.get("user", {}).get("user_id")
    return bool(uid) and uid not in (None, "")


def _is_student(inp):
    return inp.get("user", {}).get("role") == "student"


def _is_admin(inp):
    return inp.get("user", {}).get("role") == "admin"


def _is_read_method(inp):
    return inp.get("method") in {"GET", "HEAD"}


def _is_self_access(inp):
    sid = inp.get("query", {}).get("student_id")
    if not sid:
        return True
    return sid == inp.get("user", {}).get("user_id")


def _is_suspicious_grades(inp):
    ctx = inp.get("context", {})
    if ctx.get("recent_request_count", 0) > 20:
        return True
    if _is_student(inp) and 2 <= ctx.get("hour", 12) <= 5 and ctx.get("recent_request_count", 0) > 5:
        return True
    return False


def _is_suspicious_registrations(inp):
    return inp.get("context", {}).get("recent_request_count", 0) > 20


def evaluate_auth(inp):
    if not _is_from_gateway(inp):
        return False
    return inp.get("path") in {
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/session",
    }


def evaluate_profile(inp):
    if not (_is_from_gateway(inp) and _is_logged_in(inp) and _is_read_method(inp)):
        return False
    if _is_student(inp) and _is_self_access(inp):
        return True
    if _is_admin(inp):
        return True
    return False


def evaluate_grades(inp):
    if not (_is_from_gateway(inp) and _is_logged_in(inp) and _is_read_method(inp)):
        return False
    if _is_suspicious_grades(inp):
        return False
    if _is_student(inp) and _is_self_access(inp):
        return True
    if _is_admin(inp):
        return True
    return False


def evaluate_enrollments(inp):
    if not (_is_from_gateway(inp) and _is_logged_in(inp) and _is_read_method(inp)):
        return False
    if _is_student(inp) and _is_self_access(inp):
        return True
    if _is_admin(inp):
        return True
    return False


def evaluate_registrations(inp):
    if not (_is_from_gateway(inp) and _is_logged_in(inp) and _is_read_method(inp)):
        return False
    if _is_suspicious_registrations(inp):
        return False
    if _is_student(inp) and _is_self_access(inp):
        return True
    if _is_admin(inp):
        return True
    return False


EVALUATORS = {
    "guardians/auth": evaluate_auth,
    "guardians/profile": evaluate_profile,
    "guardians/grades": evaluate_grades,
    "guardians/enrollments": evaluate_enrollments,
    "guardians/registrations": evaluate_registrations,
}
