#
# gateway Dockerfile - API Gateway
# ─────────────────────────────────
# SPIFFE ID: spiffe://guardians.local/service/gateway
#   docker build -f gateway/Dockerfile -t guardians/gateway .
#
# 프론트엔드 정적 파일도 함께 서빙합니다.
#
FROM python:3.11

WORKDIR /app

# pyspiffe → grpcio 가 wheel 없는 경우를 대비해 빌드 툴 설치.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ python3-dev libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY gateway/ /app/
COPY frontend/ /app/frontend/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/shared/requirements.txt \
 && pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
