# ---------- Build stage ----------
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Runtime stage ----------
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy app
COPY app ./app
COPY tests ./tests

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_NAME=all-MiniLM-L6-v2 \
    ROUTER_PATH=/app/data/router.joblib \
    DATABASE_PATH=/app/data/rbf_router.db

# Create writable data dir
RUN mkdir -p /app/data

EXPOSE 8080

# Cloud Run expects the container to listen on $PORT (default 8080)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
