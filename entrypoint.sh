#!/bin/sh
set -e

python3 manage.py makemigrations
echo "Apply database migrations"
python3 manage.py migrate --noinput

echo "Collect static files"
python3 manage.py collectstatic --noinput

echo "Starting Django server with Uvicorn..."
exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000
