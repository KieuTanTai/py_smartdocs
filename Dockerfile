# ============================================================
# SmartDocs Production Dockerfile
# ============================================================
# Multi-stage build:
#   - builder: install dependencies
#   - production: runtime image
# ============================================================
FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements/base.txt /app/requirements.txt
RUN pip install --no-cache-dir --user -r /app/requirements.txt

# ── Production stage ────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmariadb3 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV TMPDIR=/shared-tmp
ENV TMP=/shared-tmp
ENV TEMP=/shared-tmp

COPY . /app/

RUN mkdir -p \
    /app/storage/media \
    /app/backend/metadata/faiss_memory \
    /app/backend/metadata/docs \
    /app/backend/metadata/images \
    /app/backend/metadata/temp \
    /app/docs/logs \
    /shared-tmp && \
    chmod -R 755 /app

EXPOSE 8000

CMD ["gunicorn", "app.asgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--access-logfile", "-", "--error-logfile", "-"]
