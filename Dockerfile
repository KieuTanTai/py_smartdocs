# ============================================================
# SmartDocs Production Dockerfile
# ============================================================
# Multi-stage build:
#   - builder: install dependencies
#   - production: runtime image
# ============================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Production stage ────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/storage/media /app/metadata/faiss /app/metadata/docs /app/logs && \
    chmod -R 755 /app

EXPOSE 8000

# Run as non-root user for security
RUN useradd --create-home --shell /bin/bash smartdocs
USER smartdocs
WORKDIR /app

CMD ["gunicorn", "app.asgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
