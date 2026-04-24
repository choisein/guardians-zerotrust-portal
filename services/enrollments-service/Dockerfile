#
# enrollments-service Dockerfile - 수강내역조회
# ──────────────────────────────────────────────
# SPIFFE ID: spiffe://guardians.local/service/enrollments
#   docker build -f services/enrollments-service/Dockerfile -t guardians/enrollments-service .
#
FROM python:3.11

WORKDIR /app

# pyspiffe → grpcio 가 wheel 없는 경우를 대비해 빌드 툴 설치.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ python3-dev libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/enrollments-service/ /app/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/shared/requirements.txt

EXPOSE 5004

CMD ["python", "app.py"]
