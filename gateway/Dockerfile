#
# gateway Dockerfile - API Gateway
# ─────────────────────────────────
# SPIFFE ID: spiffe://guardians.local/service/gateway
#   docker build -f gateway/Dockerfile -t guardians/gateway .
#
# 프론트엔드 정적 파일도 함께 서빙합니다.
# critical_violation 탐지 시 spire-server CLI 를 docker exec 로 호출하기 위해
# docker CLI 를 함께 설치합니다. (소켓은 docker-compose 에서 마운트)
#
FROM python:3.11

WORKDIR /app

# 빌드 도구 + docker CLI 설치
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        gcc g++ python3-dev libffi-dev libssl-dev \
        ca-certificates curl gnupg \
 && install -m 0755 -d /etc/apt/keyrings \
 && curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
 && chmod a+r /etc/apt/keyrings/docker.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
        > /etc/apt/sources.list.d/docker.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends docker-ce-cli \
 && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY gateway/ /app/
COPY frontend/ /app/frontend/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/shared/requirements.txt \
 && pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
