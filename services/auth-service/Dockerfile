#
# auth-service Dockerfile
# ────────────────────────
# SPIFFE ID: spiffe://guardians.local/service/auth
# 빌드 컨텍스트: 프로젝트 루트
#   docker build -f services/auth-service/Dockerfile -t guardians/auth-service .
#
FROM python:3.11

WORKDIR /app

# pyspiffe → grpcio 가 wheel 없는 경우를 대비해 빌드 툴 설치.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ python3-dev libffi-dev \
 && rm -rf /var/lib/apt/lists/*

# shared + 서비스 소스 복사
COPY shared/ /app/shared/
COPY services/auth-service/ /app/

# 의존성 설치 (shared 와 서비스 공통)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/shared/requirements.txt

EXPOSE 5001

# SPIRE Agent 소켓 마운트는 docker-compose에서 볼륨으로 주입
CMD ["python", "app.py"]
