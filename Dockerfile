# Dragofactu - Multi-stage Dockerfile
# Stage 1: Build frontend, Stage 2: Python backend + static files

# ---- Stage 1: Frontend Build ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Backend + Frontend Static ----
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/app/ ./app/

# Copy frontend build output as static files
COPY --from=frontend-build /app/frontend/dist ./static

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Railway provides PORT env var - default to 8000 for local
ENV PORT=8000

# Use shell form to expand $PORT variable
CMD /bin/sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
