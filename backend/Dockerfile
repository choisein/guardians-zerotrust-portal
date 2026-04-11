FROM python:3.12-slim

WORKDIR /app

# 백엔드 파일 복사
COPY backend/ ./backend/

# 프론트엔드 파일 복사 (Flask가 ../frontend/ 경로로 참조)
COPY frontend/ ./frontend/

# 패키지 설치 (Requirements.txt 오타 반영)
RUN pip install --no-cache-dir -r ./backend/Requrements.txt

WORKDIR /app/backend

EXPOSE 5000

CMD ["python", "app.py"]
