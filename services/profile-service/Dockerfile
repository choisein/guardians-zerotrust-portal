#
# profile-service Dockerfile - 학적조회
# ──────────────────────────────────────
# SPIFFE ID: spiffe://guardians.local/service/profile
#   docker build -f services/profile-service/Dockerfile -t guardians/profile-service .
#
FROM python:3.11

WORKDIR /app

# pyspiffe → grpcio 가 wheel 없는 경우를 대비해 빌드 툴 설치.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ python3-dev libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/profile-service/ /app/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/shared/requirements.txt

EXPOSE 5002

CMD ["python", "app.py"]
