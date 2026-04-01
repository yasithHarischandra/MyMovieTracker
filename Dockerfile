# --- Stage 1: Build Frontend ---
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Final Image ---
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn uvicorn

# Copy backend code
COPY backend/ ./

# Copy frontend build from Stage 1
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html

# Nginx config
COPY docker/nginx.conf /etc/nginx/sites-available/default
# Entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Environment variables defaults
ENV DATABASE_URL=sqlite+aiosqlite:////data/mediatracker.db
ENV PORT=80

# Create data directory
RUN mkdir -p /data

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
