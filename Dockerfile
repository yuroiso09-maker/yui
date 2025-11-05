# OTIS - Optimization and Transformation Intelligence System
# Production Docker Image

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV OTIS_CONFIG_PATH=/app/config
ENV OTIS_DATA_PATH=/app/data

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    htop \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Create data directories
RUN mkdir -p /app/data /app/logs && \
    chmod 755 /app/scripts/*.py

# Create non-root user for security
RUN useradd -m -u 1000 otis && \
    chown -R otis:otis /app
USER otis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from core.main import OTISCore; print('OK')" || exit 1

# Expose ports (if needed for web interface)
EXPOSE 8080

# Default command
CMD ["python", "scripts/start_full_system.py"]

# Labels
LABEL maintainer="OTIS Development Team"
LABEL version="1.0.0"
LABEL description="OTIS - Linux Performance Optimization Suite"
LABEL org.opencontainers.image.title="OTIS"
LABEL org.opencontainers.image.description="Optimization and Transformation Intelligence System for Linux"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="OTIS Project"