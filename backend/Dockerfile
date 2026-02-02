# Dragofactu API - Dockerfile
# For both development and production

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Railway provides PORT env var)
EXPOSE 8000

# Environment variable for port (Railway overrides this)
ENV PORT=8000

# Default command - uses PORT env var for Railway compatibility
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
