# Dragofactu API - Dockerfile
# For Railway deployment

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Railway provides PORT env var - default to 8000 for local
ENV PORT=8000

# Use shell form to expand $PORT variable
CMD /bin/sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
