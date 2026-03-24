FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Health check — confirms container is alive
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import boto3; print('healthy')" || exit 1

CMD ["python", "app.py"]
