# Multi-stage Dockerfile for Team Formation Application
# Combines Vue.js frontend build and Python FastAPI backend

# Stage 1: Build Vue.js frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY ui/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY ui/ ./

# Build frontend for production
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ortools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy Python package files
COPY pyproject.toml README.md LICENSE ./
COPY team_formation/ ./team_formation/

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Install the package and dependencies
RUN uv pip install --system --no-cache .

# Copy built frontend from previous stage
COPY --from=frontend-builder /frontend/dist ./ui/dist

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=true

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["python", "-m", "uvicorn", "team_formation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
