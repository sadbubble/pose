FROM python:3.11-slim

WORKDIR /app/pose-api
COPY pose/pose-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pose/pose-api/ .
COPY pose/ /app/pose/

ENV DB_PATH=/data/pose.db
VOLUME /data
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
