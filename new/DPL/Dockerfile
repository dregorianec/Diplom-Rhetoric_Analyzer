# ============================================
# DPL: Political Rhetoric Analyzer
# CPU Version
# ============================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    git-lfs \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Копируем requirements
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src ./src
COPY README.md .
COPY env.example .

# Создаём директории
RUN mkdir -p /app/data/videos \
             /app/data/transcripts \
             /app/data/results \
             /app/models/whisper

# Volumes
VOLUME ["/app/data", "/app/models"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.config; print('OK')" || exit 1

# Entry point
ENTRYPOINT ["python", "-m", "src.app"]
CMD ["--help"]
