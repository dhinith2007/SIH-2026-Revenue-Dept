# ==============================================================================
# Revenue & Forest Department Service - Backend Dockerfile (Phase 01)
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL client and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose FastAPI backend port
EXPOSE 8000

# Healthcheck probe
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
