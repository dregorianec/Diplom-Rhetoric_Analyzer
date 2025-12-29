# Political Rhetoric Analyzer

Микросервисная платформа для анализа риторики политиков на основе YouTube видео.

## 🏗️ Архитектура

```
[YouTube] → [Ingest] → [Transcribe] → [Analyze] → [Dashboard]
                ↓           ↓             ↓
           [PostgreSQL + Redis + MinIO]
```

### Микросервисы:

1. **Ingest Service** (`:8001`) - Скачивание видео с YouTube
2. **Transcribe Service** (`:8002`) - Транскрибация речи (Whisper)
3. **Analyze Service** (`:8003`) - Детекция риторических паттернов
4. **Dashboard** (`:8501`) - Web UI (Streamlit)
5. **Celery Worker** - Фоновые задачи

### Инфраструктура:

- **PostgreSQL** (`:5432`) - База данных
- **Redis** (`:6379`) - Очереди и кэш
- **MinIO** (`:9000`, `:9001`) - Хранилище файлов

## 🚀 Быстрый старт

### Требования:

- Docker & Docker Compose
- 4GB+ RAM
- 10GB+ свободного места

### Запуск:

```bash
# Клонировать репозиторий
git clone <repo-url>
cd "DIPL NOV"

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f
```

### Доступ к сервисам:

- **Dashboard**: http://localhost:8501
- **Ingest API**: http://localhost:8001/docs
- **Transcribe API**: http://localhost:8002/docs
- **Analyze API**: http://localhost:8003/docs
- **MinIO Console**: http://localhost:9001 (admin: minio_admin / minio_password)

## 📁 Структура проекта

```
project/
├── services/
│   ├── ingest/           # YouTube download service
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── transcribe/       # Whisper ASR service
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── analyze/          # Rhetoric detection service
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── dashboard/        # Streamlit UI
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
├── shared/               # Shared code
│   ├── schemas.py        # Pydantic models
│   ├── database.py       # DB connection
│   └── storage.py        # MinIO client
├── docker-compose.yml    # Docker orchestration
├── WORK_PLAN.md         # Work plan
└── README.md            # This file
```

## 🔧 Разработка

### Локальный запуск (без Docker):

```bash
# Установить PostgreSQL, Redis локально

# Для каждого сервиса:
cd services/ingest
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Тестирование API:

Swagger UI доступен для каждого сервиса:
- Ingest: http://localhost:8001/docs
- Transcribe: http://localhost:8002/docs
- Analyze: http://localhost:8003/docs

### Health Checks:

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## 📊 API Примеры

### 1. Поиск видео

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Donald Trump", "max_results": 10}'
```

### 2. Скачать видео

```bash
curl -X POST http://localhost:8001/download \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=...",
    "politician_name": "Donald Trump"
  }'
```

### 3. Получить статус задачи

```bash
curl http://localhost:8001/task/{task_id}
```

## 🗺️ Дорожная карта

- [x] Базовая структура микросервисов
- [x] Docker Compose конфигурация
- [x] Pydantic схемы
- [ ] YouTube API интеграция
- [ ] yt-dlp скачивание
- [ ] Whisper транскрибация
- [ ] Rule-based детекция
- [ ] ML классификация
- [ ] RAG система
- [ ] LLM объяснения
- [ ] Dashboard UI
- [ ] Тесты
- [ ] Документация

## 📝 TODO (Неделя 1)

- [ ] Протестировать docker-compose up
- [ ] Добавить инициализацию БД (Alembic migrations)
- [ ] Настроить GitHub Actions CI
- [ ] Создать .env файл для конфигурации
- [ ] Добавить логирование

## 🤝 Контрибуция

Проект в активной разработке. Pull requests приветствуются!

## 📄 Лицензия

MIT

