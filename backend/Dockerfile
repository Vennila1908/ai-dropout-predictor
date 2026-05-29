# ─── Build a slim production image for the FastAPI backend ───
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System deps: build-essential is needed only by some wheels (xgboost, lxml, etc.).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq5 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first to maximize Docker layer caching.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app source.
COPY . /app

# Runtime data dirs (also mounted as volumes in docker-compose.yml).
RUN mkdir -p /app/uploads /data /app/ml_artifacts \
    && chmod -R 755 /app

ENV ML_ARTIFACT_DIR=/app/ml_artifacts \
    UPLOAD_DIR=/app/uploads \
    DATABASE_URL=sqlite:////data/app.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
