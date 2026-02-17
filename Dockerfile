# ─────────────────────────────────────────────────────────────────────────────
# SoundPixel — Docker image
# Multi-stage: build React, then serve via Flask + Gunicorn
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --legacy-peer-deps
COPY frontend/ ./
RUN npm run build


# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Run codec tests at build time (fail-fast if broken)
RUN python backend/test_codec.py

EXPOSE 5000

ENV PORT=5000
ENV WORKERS=2
ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1

CMD gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WORKERS}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    "backend.server:app"
