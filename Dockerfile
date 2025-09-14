# syntax=docker/dockerfile:1
FROM python:3.11-slim

# System deps for matplotlib + optional ruckig build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libfreetype6 \
    libpng16-16 \
    fonts-dejavu-core \
    curl \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

EXPOSE 8000 8501

CMD ["bash", "-lc", "python -c 'print(\"Image built. Use docker compose to run services.\")'"]
