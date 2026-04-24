# Guardians Zero-Trust Portal

SPIRE + OPA 기반 마이크로서비스형 제로트러스트 학생 포털.

기존 모놀리식 `backend/routes/student.py` 를 기능별로 분리하여, **서비스별로 독립된 SVID(SPIFFE Verifiable Identity Document)** 를 발급받을 수 있도록 재구성했습니다.

## 아키텍처 개요

```
  [Browser]
      │ HTTPS
      ▼
┌───────────────────────────────────────────────────────┐
│  Gateway  (spiffe://guardians.local/service/gateway)  │
│  - 경로별로 요청 라우팅                                 │
│  - 자신의 JWT-SVID를 X-SVID 헤더에 첨부                │
└───────────────────────────────────────────────────────┘
      │   │   │   │   │
      ▼   ▼   ▼   ▼   ▼
  auth  profile  grades  enrollments  registrations
  :5001  :5002    :5003    :5004         :5005
  │       │       │        │             │
  └───────┴───────┴────────┴─────────────┘
                   │
           각 서비스는 개별 SPIFFE ID 보유
           요청마다 SVID 검증 + OPA 인가 질의
                   │
   ┌───────────────┼───────────────┐
   ▼               ▼               ▼
SPIRE Server   SPIRE Agent         OPA
(CA/Control)   (Workload API)  (Policy Decision)
```

## SPIFFE ID 할당

| 서비스 | 기능 | SPIFFE ID | 포트 |
|---|---|---|---|
| gateway | 프론트엔드/프록시 | `spiffe://guardians.local/service/gateway` | 5000 |
| auth-service | 로그인 | `spiffe://guardians.local/service/auth` | 5001 |
| profile-service | 학적조회 | `spiffe://guardians.local/service/profile` | 5002 |
| grades-service | 성적조회 | `spiffe://guardians.local/service/grades` | 5003 |
| enrollments-service | 수강내역조회 | `spiffe://guardians.local/service/enrollments` | 5004 |
| registrations-service | 등록금납부조회 | `spiffe://guardians.local/service/registrations` | 5005 |

## 디렉터리 구조

```
guardians-zerotrust-portal/
├── shared/                         # 공통 모듈 (모든 서비스에 주입)
│   ├── models.py                   # SQLAlchemy 모델
│   ├── config.py                   # 공통 Config
│   ├── spire_client.py             # SPIRE Workload API 래퍼
│   ├── opa_client.py               # OPA HTTP 클라이언트
│   ├── middleware.py               # @zero_trust_required 데코레이터
│   └── requirements.txt            # 파이썬 의존성
│
├── gateway/                        # API Gateway
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── services/
│   ├── auth-service/               # 로그인
│   │   ├── app.py
│   │   ├── routes/auth.py
│   │   └── Dockerfile
│   ├── profile-service/            # 학적조회
│   │   ├── app.py
│   │   ├── routes/profile.py
│   │   └── Dockerfile
│   ├── grades-service/             # 성적조회
│   │   ├── app.py
│   │   ├── routes/grades.py
│   │   └── Dockerfile
│   ├── enrollments-service/        # 수강내역조회
│   │   ├── app.py
│   │   ├── routes/enrollments.py
│   │   └── Dockerfile
│   └── registrations-service/      # 등록금납부조회
│       ├── app.py
│       ├── routes/registrations.py
│       └── Dockerfile
│
├── spire/
│   ├── server/server.conf          # SPIRE Server 설정
│   ├── agent/agent.conf            # SPIRE Agent 설정
│   └── scripts/
│       ├── bootstrap-agent.sh      # Agent join token 발급
│       └── register-workloads.sh   # 서비스별 SPIFFE ID 등록
│
├── opa/policies/                   # (Rego 정책 파일을 여기에 추가)
│
├── frontend/                       # 기존 HTML/CSS/JS (그대로 사용)
├── db/                             # 초기 SQL 스크립트
├── backend/                        # (레거시, 참고용)
└── docker-compose.yml
```

## 실행 방법

### 1. 최초 기동 (부트스트랩)

SPIRE 공식 이미지는 distroless (쉘 없음) 라서, 부트스트랩 명령은 **호스트(PowerShell)에서** 실행합니다.

```powershell
# 1) SPIRE Server 먼저 기동
docker compose up -d spire-server

# 2) Join Token 생성 → .env 에 JOIN_TOKEN 자동 기록
powershell -ExecutionPolicy Bypass -File .\spire\scripts\bootstrap-agent.ps1

# 3) SPIRE Agent 기동 (compose 가 .env 의 JOIN_TOKEN 을 주입)
docker compose up -d spire-agent

# 4) 서비스별 SPIFFE 엔트리 등록
powershell -ExecutionPolicy Bypass -File .\spire\scripts\register-workloads.ps1

# 5) 나머지 서비스 모두 기동
docker compose up -d
```

> Linux/macOS 에서는 `spire/scripts/bootstrap-agent.sh`, `register-workloads.sh` 를 참고해 동일한 명령을 `docker compose exec -T spire-server /opt/spire/bin/spire-server ...` 형태로 실행하시면 됩니다.

### 2. 동작 확인

```bash
# 게이트웨이 health
curl http://localhost:5000/health

# 로그인 요청 (게이트웨이를 통해서만 가능, SVID 자동 첨부됨)
curl -X POST http://localhost:5000/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"user_id":"user_202300001","password":"test1234"}'

# SVID 발급 확인 (Agent 컨테이너에서 직접 요청)
docker compose exec spire-agent /opt/spire/bin/spire-agent api fetch jwt \
    -audience spiffe://guardians.local/service/profile \
    -socketPath /run/spire/agent/public/api.sock
```

## 제로트러스트 요청 흐름

모든 요청은 다음 순서로 검증됩니다 (`shared/middleware.py`):

1. **SVID 검증** — 요청 헤더의 `X-SVID`(JWT)를 SPIRE Workload API로 검증. 호출자 SPIFFE ID 추출.
2. **세션 검증** — 로그인 서비스 제외, 모든 엔드포인트는 Flask 세션 필요.
3. **OPA 인가** — `caller_spiffe_id`, `user.role`, `method`, `path` 를 OPA에 보내 allow/deny 결정.

> OPA 정책(Rego)은 이번 작업 범위에서 제외되어 있습니다. `opa/policies/` 폴더에 직접 추가하시면 됩니다. 예시 패키지명은 각 서비스의 `@zero_trust_required(policy_package=...)` 에 지정되어 있습니다:
> - `guardians/auth`, `guardians/profile`, `guardians/grades`, `guardians/enrollments`, `guardians/registrations`

## API 엔드포인트

게이트웨이(`:5000`)를 통해 외부로 노출되는 경로는 기존과 동일합니다.

| 메서드 | 경로 | 라우팅 대상 |
|---|---|---|
| POST | /api/auth/login | auth-service |
| POST | /api/auth/logout | auth-service |
| GET  | /api/auth/session | auth-service |
| GET  | /api/student/profile | profile-service |
| GET  | /api/student/grades | grades-service |
| GET  | /api/student/grades/&lt;semester&gt; | grades-service |
| GET  | /api/student/enrollments | enrollments-service |
| GET  | /api/student/registrations | registrations-service |

## 레거시 `backend/` 폴더

기존 모놀리식 코드는 `backend/` 에 그대로 남아있습니다. 마이그레이션이 완료되면 제거해도 무방합니다.
