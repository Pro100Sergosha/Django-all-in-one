#!/bin/sh
set -e

python3 manage.py makemigrations
echo "Apply database migrations"
python3 manage.py migrate --noinput

echo "Collect static files"
python3 manage.py collectstatic --noinput

echo "Starting Django server with Uvicorn..."
exec gunicorn config.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 4 \
  --worker-connections 1000

