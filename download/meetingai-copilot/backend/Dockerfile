# ---------------------------------------------------------------------------
# MeetingAI Copilot - Backend Dockerfile
# Multi-stage build for optimized production image
# ---------------------------------------------------------------------------

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-time system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies into a separate directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Production image
FROM python:3.12-slim

LABEL maintainer="MeetingAI Copilot Team"
LABEL description="FastAPI backend for MeetingAI Copilot"

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r meetingai && \
    useradd -r -g meetingai -d /app -s /sbin/nologin meetingai

# Create uploads directory and set ownership
RUN mkdir -p /app/uploads && \
    chown -R meetingai:meetingai /app

# Switch to non-root user
USER meetingai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
