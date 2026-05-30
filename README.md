# Guardians Zero-Trust Portal

SPIRE(SPIFFE) + OPA 기반 마이크로서비스 제로트러스트 학생 포털.
각 서비스는 독립된 SVID 신원을 갖고, 모든 요청은 **SVID 검증 + OPA 인가**를 거친다.
핵심 목표는 **침해된 서비스의 횡적 이동(lateral movement)을 SVID 즉시 폐지로 차단**하는 것.

## 시스템 아키텍처 흐름

평상시 요청 흐름:

```
                       ┌─────────────────────┐
                       │       Browser       │
                       └──────────┬──────────┘
                                  │ HTTPS + session cookie
                                  ▼
╔══════════════════════════════════════════════════════════════════╗
║          Gateway  :5000  (spiffe://.../service/gateway)          ║
║   경로 라우팅 + audience=대상 서비스로 SVID 발급해 X-SVID 첨부      ║
╚════╤═══════════════╤══════════════╤═══════════════╤══════════════╝
     │               │              │               │
     ▼               ▼              ▼               ▼
 ┌────────┐    ┌─────────┐    ┌────────┐    ┌─────────────┐    ┌──────────────┐
 │  auth  │    │ profile │    │ grades │    │ enrollments │    │registrations │
 │ :5001  │    │  :5002  │    │ :5003  │    │   :5004     │    │   :5005      │
 └────────┘    └─────────┘    └────────┘    └─────────────┘    └──────────────┘

각 서비스 미들웨어:
  ① X-SVID 검증 + blocklist 확인
  ② source / caller_service 파생
  ③ Flask 세션 확인
  ④ OPA(:8181) 평가

제어 평면:
  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
  │  SPIRE Server  │◀─▶│  SPIRE Agent   │   │   OPA :8181    │
  │  (entry CRUD)  │   │ (Workload API) │   │  (rego policy) │
  └────────────────┘   └────────────────┘   └────────────────┘
```

critical_violation 폐지 + Failover 시퀀스:

```
[1] 횡적 이동 시도 (예: profile → grades)
    profile  ──자기 SVID(aud=grades)──▶  grades

[2] grades 측 OPA 가 critical_violation 판정
                │
                ▼
       middleware 가 두 가지를 동시에 수행
        ├─ revoke_entry(profile)        ← SPIRE entry 삭제 + 블록리스트
        └─ POST http://revocation-store:6000/revoke

[3] revocation-store 가 공유 볼륨에 기록
                │
                ▼
        revocation-data 볼륨
        └─ profile.revoked

[4] 이후 브라우저 → Gateway 요청
                │
       Gateway 가 revocation-data 확인
                │
                ▼
    /profile 트래픽을 profile-replica 로 우회
    SVID audience = spiffe://.../service/profile-replica
                │
                ▼
        profile-replica (독립 SPIFFE ID, 정상 검증 통과)
        → 사용자에게 정상 응답 (포털 가용성 유지)
```

## 서비스 / SPIFFE ID

| 서비스 | 기능 | SPIFFE ID | 포트 |
|---|---|---|---|
| gateway | 프록시/진입점 | `.../service/gateway` | 5000 |
| auth-service | 로그인 | `.../service/auth` | 5001 |
| profile-service | 학적조회 | `.../service/profile` | 5002 |
| grades-service | 성적조회 | `.../service/grades` | 5003 |
| enrollments-service | 수강내역조회 | `.../service/enrollments` | 5004 |
| registrations-service | 등록금조회 | `.../service/registrations` | 5005 |

(trust domain: `guardians.local`)

추가로 각 주요 서비스의 **replica**(`.../service/<svc>-replica`, 폐지 시 우회 대상)와 폐지 기록용 **revocation-store**(`:6000`)가 있다.

## 두 개의 신뢰 계층

- **사용자 계층 (외부, 게이트웨이 경유)** — 브라우저 요청은 게이트웨이가 자기 SVID를 붙여 프록시한다. 수신측은 `source="gateway"`. 로그인·본인 데이터·역할로 통제하며, 위반 시 **deny**(접근 통제).
- **워크로드 계층 (서비스 간 직접 호출)** — 서비스가 자기 SVID로 다른 서비스를 직접 호출한다. 수신측은 `source="service"` + `caller_service`. **호출 그래프**로 통제하며, 그래프 이탈 시 **critical_violation → SVID 즉시 폐지**.


## 허용 호출 그래프

| 호출자 → 대상 | 용도 |
|---|---|
| gateway → 전체 | 외부 진입점 |
| enrollments → grades | 선수과목 확인 (읽기) |
| enrollments → profile | 수강 자격 확인 (읽기) |
| registrations → enrollments | 등록금 산정 (읽기) |

그 외 모든 서비스 간 직접 호출은 그래프 이탈로 간주한다.

## 제로트러스트 요청 흐름 (`shared/middleware.py`)

1. **SVID 검증** — `X-SVID`(JWT)를 SPIRE Workload API로 검증, blocklist 확인, 호출자 SPIFFE ID 추출.
2. **출처 파생** — `caller_spiffe_id` → `source`(gateway/service) + `caller_service`(예 `enrollments-service`).
3. **세션 검증** — (로그인 서비스 제외) Flask 세션 필요.
4. **OPA 인가** — `source`, `caller_service`, `user`, `method`, `path`, `context`로 `allow` + `critical_violation` 동시 평가.
5. **대응 분기**
   - `critical_violation` → 호출 서비스의 **SVID 즉시 폐지** (`revoke_entry`: blocklist 등록 + SPIRE entry 삭제). 단 **게이트웨이 신원은 폐지하지 않음**(가드).
   - `allow == false` → 일반 **deny** (entry 유지).

## OPA 정책 (`opa/policies/`)

`common.rego`(공통 헬퍼) + 서비스별 패키지 `guardians.{auth,profile,grades,enrollments,registrations}`.

각 서비스 정책이 정의하는 것:
- **allow** — 외부(게이트웨이) 요청 + 허용된 내부 호출자(읽기).
- **is_suspicious_pattern → deny** — 대량 조회, 비정상 시간대, 본인 외 학번 조회, 학생 쓰기 등 사용자 차원 이상행동.
- **critical_violation → SVID 폐지** — 호출 그래프 이탈(A·B), 허용 서비스의 쓰기 시도(D), 내부 대량 호출(E).

> OPA는 정책을 시작 시 1회 로드한다(`--watch` 미사용). 정책 수정 후에는 OPA 재시작 필요.

## 폐지 시 Failover (복제본 우회)

critical_violation 으로 서비스의 SVID 가 폐지되면, 게이트웨이가 이후 그 서비스로 가는 요청을 **클린 복제본(replica)** 으로 우회시켜 포털 가용성을 유지한다.

- 각 주요 서비스(profile/grades/enrollments/registrations)는 **독립 SPIFFE ID** 를 가진 replica(`.../service/<svc>-replica`)를 둔다. 원본이 폐지돼 entry 가 삭제돼도 replica 신원은 살아있다.
- 폐지 탐지 시 미들웨어가 `revocation-store`(:6000)에 알리고, 게이트웨이와 공유하는 볼륨 `revocation-data` 에 `<svc>.revoked` 파일이 기록된다.
- 게이트웨이는 매 요청마다 이 파일을 확인해, 폐지된 서비스는 **replica 의 SPIFFE ID 를 audience 로 SVID 를 발급**해 replica 로 우회한다(정상 SVID 통신).

흐름 예: `profile→grades` 횡적 이동 시도 → profile SVID 폐지 → 이후 profile 요청은 `profile-replica` 가 처리(게이트웨이 로그 `[FAILOVER]`).

데모 반복 초기화: `curl -X POST http://localhost:6000/reset` (폐지 기록 삭제 → 원본으로 복귀)

## API 엔드포인트

외부(게이트웨이 `:5000`):

| 메서드 | 경로 | 대상 |
|---|---|---|
| POST | /api/auth/login, /logout | auth |
| GET | /api/auth/session | auth |
| GET | /api/student/profile | profile |
| GET | /api/student/grades[/&lt;semester&gt;] | grades |
| GET | /api/student/enrollments | enrollments |
| GET | /api/student/registrations | registrations |

서비스 간 호출 데모 (로그인 상태로 호출 → 해당 서비스가 다른 서비스를 직접 호출):

| 경로 | 호출 | 기대 결과 |
|---|---|---|
| /api/student/enrollments/internal/grades | enrollments→grades | allow |
| /api/student/enrollments/internal/profile | enrollments→profile | allow |
| /api/student/registrations/internal/enrollments | registrations→enrollments | allow |
| /api/student/profile/internal/grades | profile→grades | critical → profile SVID 폐지 |
| /api/student/registrations/internal/grades | registrations→grades | critical → registrations SVID 폐지 |

## 실행

```powershell
docker compose up -d spire-server
powershell -ExecutionPolicy Bypass -File .\spire\scripts\bootstrap-agent.ps1
docker compose up -d spire-agent
powershell -ExecutionPolicy Bypass -File .\spire\scripts\register-workloads.ps1
docker compose up -d --build
```

- 코드/정책 변경 반영: `docker compose down && docker compose up -d --build` (서비스 코드·정책은 이미지/시작 시 로드되므로 재빌드·재기동 필요).
- 횡적 이동 데모로 SVID가 폐지된 서비스는 `register-workloads` 재실행 + 해당 서비스 재시작으로 초기화.

## 디렉터리 (요약)

```
shared/        공통 모듈 (models, config, spire_client, opa_client, middleware, service_client)
gateway/       API 게이트웨이
services/      auth / profile / grades / enrollments / registrations (+ 각 *-replica, revocation-store)
opa/policies/  Rego 정책 (common + 서비스별)
spire/         SPIRE Server/Agent 설정 + 등록 스크립트
frontend/      HTML/CSS/JS
backend/       레거시 모놀리식 (참고용)
docker-compose.yml
```
