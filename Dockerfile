# ==============================================================================
# Revenue & Forest Department Service - Backend Root Dockerfile
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Expose default port
EXPOSE 8000

# Healthcheck probe
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run Uvicorn ASGI server with dynamic $PORT support
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
