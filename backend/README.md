# ⚠️ 레거시 폴더

이 디렉터리의 코드는 **모놀리식 버전**이며, 새 아키텍처에서는 더 이상 사용되지 않습니다.

새 아키텍처에서는 기능별로 아래와 같이 분리되었습니다:

| 기존 | 분리된 위치 |
|---|---|
| `backend/routes/auth.py` | `services/auth-service/routes/auth.py` |
| `backend/routes/student.py` · `get_profile` | `services/profile-service/routes/profile.py` |
| `backend/routes/student.py` · `get_grades` | `services/grades-service/routes/grades.py` |
| `backend/routes/student.py` · `get_enrollments` | `services/enrollments-service/routes/enrollments.py` |
| `backend/routes/student.py` · `get_registrations` | `services/registrations-service/routes/registrations.py` |
| `backend/models.py` · `config.py` | `shared/models.py` · `shared/config.py` |

각 서비스는 자신의 **SPIFFE ID / SVID** 를 갖습니다 (루트 `README.md` 참고).

포털 전체가 안정적으로 동작하면 이 폴더는 삭제하셔도 됩니다.
