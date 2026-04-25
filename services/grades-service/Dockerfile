#
# grades-service Dockerfile - 성적조회
# ─────────────────────────────────────
# SPIFFE ID: spiffe://guardians.local/service/grades
#   docker build -f services/grades-service/Dockerfile -t guardians/grades-service .
#
FROM python:3.11

WORKDIR /app

# spiffe 가 pull 하는 grpcio / cryptography 등이 wheel 없으면 소스 빌드로 떨어질 때를 대비.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ python3-dev libffi-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/grades-service/ /app/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/shared/requirements.txt

EXPOSE 5003

CMD ["python", "app.py"]
