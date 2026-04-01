#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting MediaTracker..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start Nginx in the background
echo "Starting Nginx..."
nginx

# Start FastAPI backend via Gunicorn
echo "Starting FastAPI backend..."
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8020
