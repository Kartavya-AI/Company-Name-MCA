FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Dependencies installed OK" \
    || (echo "Failed to install dependencies" && exit 1)

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV PYTHONPATH=/app

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["gunicorn", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "300", "--bind", "0.0.0.0:8080", "api:app"]