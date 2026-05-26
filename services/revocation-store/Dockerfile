FROM python:3.11-slim

WORKDIR /app

RUN pip install flask

COPY services/revocation-store/revocation_store.py /app/

EXPOSE 6000

CMD ["python", "revocation_store.py"]