# OPA 정책 (Guardians Zero-Trust Portal)

## 개요

이 폴더에는 5개 마이크로서비스의 인가(Authorization) 정책이 들어있습니다.
각 서비스는 요청을 받을 때마다 OPA에 "이 요청 허용해도 돼?"라고 물어보고,
OPA는 여기 정책 파일에 적힌 규칙대로 판단합니다.

## 파일 구조

```
opa/policies/
├── common.rego        # 공통 헬퍼 (호출자 검증, 역할 확인)
├── auth.rego          # 로그인 서비스 정책
├── profile.rego       # 학적조회 (민감)
├── grades.rego        # 성적조회 (가장 민감 + 이상탐지)
├── enrollments.rego   # 수강내역 조회
└── registrations.rego # 등록금납부 (민감 + 이상탐지)
```

## 정책 핵심 규칙

각 정책은 다음 4가지를 종합적으로 판단합니다.

1. **서비스 간 인증** — 호출자가 게이트웨이인지 확인
   (외부에서 마이크로서비스를 직접 호출하는 것 차단)
2. **사용자 인증** — Flask 세션이 있는지 확인
3. **역할 기반 접근 제어 (RBAC)**
   - 학생: 본인 데이터만 조회 가능
   - 관리자: 모든 데이터 조회 가능
4. **이상행동 탐지 (성적/등록금만)**
   - 10초 내 21회 이상 요청 시 차단
   - 학생이 새벽 2~5시에 6회 이상 조회 시 차단

## 실행 방법

### 1) 전체 시스템 기동

```bash
# SPIRE 셋업 (1회)
docker compose up -d spire-server
docker compose exec spire-server sh /spire/scripts/bootstrap-agent.sh
docker compose up -d spire-agent
docker compose exec spire-server sh /spire/scripts/register-workloads.sh

# OPA + 마이크로서비스 + 게이트웨이 기동
docker compose up -d
```

### 2) OPA 정책이 로드됐는지 확인

```bash
# OPA에 등록된 정책 목록 조회
curl http://localhost:8181/v1/policies | jq

# 특정 정책 직접 질의 (학생이 본인 학적 조회)
curl -X POST http://localhost:8181/v1/data/guardians/profile/allow \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "caller_spiffe_id": "spiffe://guardians.local/service/gateway",
      "user": {"user_id": "20230001", "role": "student"},
      "method": "GET",
      "path": "/api/student/profile",
      "query": {},
      "context": {"hour": 14, "recent_request_count": 1}
    }
  }'
# 기대 응답: {"result": true}
```

### 3) 데모 실행

```bash
python3 attack_demo.py
```

5가지 시나리오를 자동으로 실행해서 OPA 정책이 제대로 작동하는지 보여줍니다.

## 정책 수정 후 반영

정책 파일을 수정하면 OPA를 재시작해서 반영합니다.

```bash
docker compose restart opa
```

코드 변경은 필요 없습니다. **정책은 .rego 파일만 고치면 됩니다.**
이게 OPA를 쓰는 가장 큰 이유예요.
