#
# enrollments-service Dockerfile - 수강내역조회
# ──────────────────────────────────────────────
# SPIFFE ID: spiffe://guardians.local/service/enrollments
#   docker build -f services/enrollments-service/Dockerfile -t guardians/enrollments-service .
#
FROM python:3.11

WORKDIR /app

# spiffe 가 pull 하는 grpcio / cryptography 등이 wheel 없으면 소스 빌드로 떨어질 때를 대비.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ python3-dev libffi-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/enrollments-service/ /app/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/shared/requirements.txt

EXPOSE 5004

CMD ["python", "app.py"]
