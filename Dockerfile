# Dockerfile.backend

FROM python:3.12.4

RUN apt-get update && apt-get install -y \
    libpq-dev gcc musl-dev gettext redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/ .  
COPY entrypoint.sh /app
RUN chmod +x entrypoint.sh

RUN pip install --upgrade pip
RUN pip install -r requirements.txt


EXPOSE 8000

