# 🚀 Быстрый старт

## Шаг 1: Клонирование и переход в папку

```bash
cd "C:\Users\COLORFUL\Desktop\Cursor_prods\DIPL NOV"
```

## Шаг 2: Запуск всех сервисов

**Windows (PowerShell):**
```powershell
docker-compose up -d
```

**Linux/Mac:**
```bash
make up
# или
docker-compose up -d
```

## Шаг 3: Проверка статуса

```bash
docker-compose ps
```

Все сервисы должны быть в статусе `Up` или `healthy`.

## Шаг 4: Открыть Dashboard

Откройте в браузере: http://localhost:8501

## Шаг 5: Первый тест

1. В Dashboard выберите "Search & Submit"
2. Введите в поиск: "Donald Trump"
3. Нажмите "Search"
4. Выберите видео и нажмите "Download & Analyze"

## 📊 Доступ к сервисам

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| Dashboard | http://localhost:8501 | - |
| Ingest API | http://localhost:8001/docs | - |
| Transcribe API | http://localhost:8002/docs | - |
| Analyze API | http://localhost:8003/docs | - |
| MinIO Console | http://localhost:9001 | minio_admin / minio_password |
| PostgreSQL | localhost:5432 | rhetoric_user / rhetoric_pass |
| Redis | localhost:6379 | - |

## 🔧 Полезные команды

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f ingest
docker-compose logs -f transcribe
docker-compose logs -f analyze
docker-compose logs -f dashboard
```

### Перезапуск сервиса
```bash
docker-compose restart ingest
```

### Остановка всех сервисов
```bash
docker-compose down
```

### Полная очистка (удалит все данные!)
```bash
docker-compose down -v
```

## ❓ Проблемы?

### Порт уже занят
Если порт 5432, 6379, 8001, 8002, 8003, 8501, 9000 или 9001 уже занят:

1. Остановите приложение, использующее порт
2. Или измените порты в `docker-compose.yml`

### Сервис не стартует
```bash
# Проверить логи
docker-compose logs <service_name>

# Пересобрать образ
docker-compose build <service_name>
docker-compose up -d <service_name>
```

### База данных не инициализирована
```bash
# Пересоздать volume
docker-compose down -v
docker-compose up -d
```

## 📝 Следующие шаги

1. ✅ Все работает? Переходи к реализации функциональности!
2. 📖 Смотри `WORK_PLAN.md` для плана работ
3. 🔨 Начни с Недели 2-3: YouTube API integration

## 🆘 Нужна помощь?

- Проверь `README.md` для детальной информации
- Проверь логи: `docker-compose logs -f`
- Проверь health endpoints: http://localhost:8001/health

