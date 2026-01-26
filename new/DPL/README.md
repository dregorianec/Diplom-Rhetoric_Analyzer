# DPL: Political Rhetoric Analyzer

Анализатор риторических ошибок в речи политиков.

**Поток данных:**
```
[Имя политика] → [YouTube Search] → [Download] → [Whisper ASR] → [LLM Analysis] → [Графики]
```

---

## 🐳 Запуск через Docker (рекомендуется)

### 1. Подготовка

```bash
cd new/DPL

# Копировать .env (отредактировать при необходимости)
copy env.example .env
```

### 2. Скачать модель Whisper

```bash
cd models/whisper
git lfs install
git clone https://huggingface.co/openai/whisper-large-v3 .
cd ../..
```

### 3. Запустить LM Studio на хосте

1. Скачать [LM Studio](https://lmstudio.ai/)
2. Загрузить модель `openai/gpt-oss-20b`
3. Запустить сервер на порту `1234`

### 4. Собрать и запустить

```bash
# Собрать образ (CPU версия)
docker-compose build dpl

# Запустить анализ
docker-compose run --rm dpl analyze -p "Donald Trump"

# С расширенным каталогом ошибок
docker-compose run --rm dpl analyze -p "Vladimir Putin" --extended

# Анализ готового транскрипта
docker-compose run --rm dpl legacy -t data/transcripts/speech.txt

# Визуализация
docker-compose run --rm dpl visualize -r data/results/analysis-2024-01-01.json

# Открыть shell в контейнере
docker-compose run --rm dpl /bin/bash
```

### GPU версия (NVIDIA CUDA)

```bash
# Собрать GPU образ
docker-compose --profile gpu build dpl-gpu

# Запустить с GPU
docker-compose --profile gpu run --rm dpl-gpu analyze -p "Donald Trump"
```

### Использование Makefile (Windows/Linux)

```bash
# Показать все команды
make help

# Начальная настройка
make setup

# Собрать образ
make build

# Запустить анализ
make analyze p="Donald Trump"

# С расширенным каталогом
make analyze-extended p="Vladimir Putin"

# Shell в контейнере
make shell
```

### Использование PowerShell скрипта (Windows)

```powershell
# Показать помощь
.\scripts\docker-run.ps1

# Собрать образ
.\scripts\docker-run.ps1 build

# Запустить анализ
.\scripts\docker-run.ps1 analyze -p "Donald Trump"

# Shell
.\scripts\docker-run.ps1 shell
```

---

## 🚀 Локальный запуск (без Docker)

### 1. Подготовка окружения

```bash
cd new/DPL

# Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
# или: source venv/bin/activate  # Linux/Mac

# Установить зависимости
pip install -r requirements.txt

# Скопировать .env
copy env.example .env
```

### 2. Установка модели Whisper

```bash
cd models/whisper
git lfs install
git clone https://huggingface.co/openai/whisper-large-v3 .
cd ../..
```

### 3. Запуск

```bash
python -m src.app analyze --politician "Donald Trump"
```

---

## 📁 Структура проекта

```
DPL/
├── models/
│   └── whisper/              # Модель Whisper (клонировать!)
├── data/
│   ├── videos/               # Скачанные видео/аудио
│   ├── transcripts/          # Транскрипты
│   └── results/              # JSON + графики
├── src/
│   ├── app.py                # CLI entry point
│   ├── config.py             # Конфигурация
│   ├── domain/               # Модели и интерфейсы
│   ├── infrastructure/       # Адаптеры (YouTube, Whisper, LLM)
│   └── application/          # Бизнес-логика
├── scripts/
│   ├── docker-run.sh         # Linux/Mac скрипт
│   └── docker-run.ps1        # Windows скрипт
├── Dockerfile                # CPU версия
├── Dockerfile.gpu            # GPU версия
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── env.example
```

---

## ⚙️ Конфигурация (.env)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `LLM_API_KEY` | API ключ LLM | `lm-studio-placeholder` |
| `LLM_API_BASE` | URL LLM сервера | `http://127.0.0.1:1234/v1` |
| `LLM_MODEL` | Модель | `openai/gpt-oss-20b` |
| `RAPIDAPI_KEY` | Ключ RapidAPI | `your-key` |
| `WHISPER_MODEL_PATH` | Путь к Whisper | `./models/whisper` |
| `WHISPER_DEVICE` | Устройство | `cuda` / `cpu` |
| `WHISPER_LANGUAGE` | Язык | `en` / `ru` / `auto` |

**Важно для Docker:** LM Studio запущен на хосте, поэтому в контейнере используется `host.docker.internal:1234`.

---

## 🔍 CLI команды

```bash
# Полный пайплайн
python -m src.app analyze --politician "NAME" [--extended] [--max-videos N]

# Анализ готового транскрипта
python -m src.app legacy --transcript-path FILE [--extended]

# Визуализация результатов
python -m src.app visualize --results-file FILE [--politician NAME]
```

### Флаги:

| Флаг | Описание |
|------|----------|
| `-p, --politician` | Имя политика для поиска |
| `-n, --max-videos` | Количество видео (default: 1) |
| `-e, --extended` | Расширенный каталог (15 типов ошибок) |
| `-t, --transcript-path` | Путь к транскрипту |
| `-r, --results-file` | Путь к JSON результатам |
| `--no-plot` | Не показывать графики |
| `--save-plot-only` | Только сохранить графики |

---

## 📊 Детектируемые ошибки

### Базовый каталог (5 типов):
- **Ad Hominem** — Атака на личность
- **Straw Man** — Искажение аргумента оппонента
- **Complex Question** — Многовопросие
- **False Accusation** — Ложное обвинение
- **Hyperbole** — Преувеличение

### Расширенный каталог (`--extended`, 15 типов):
+ Change of Subject, Insinuation, False Suspicion, Categorical Disagreement,
  Authoritarian Style, Lady's Argument, Imposed Consequence, Fact Sifting,
  Suspicion Construction, Ironic Repetition

---

## 🛠️ Требования

### Docker версия:
- Docker Desktop 4.0+
- ~10 GB для образа + модель Whisper
- NVIDIA Docker (для GPU версии)

### Локальная версия:
- Python 3.10+
- FFmpeg
- ~6 GB VRAM для Whisper (GPU)
- LM Studio

---

## 🐛 Troubleshooting

**Docker: Cannot connect to LM Studio**
- Убедитесь, что LM Studio запущен на хосте
- Проверьте порт 1234
- Для Windows/Mac используется `host.docker.internal`
- Для Linux добавьте `--add-host=host.docker.internal:host-gateway`

**CUDA out of memory**
- Используйте CPU версию: `WHISPER_DEVICE=cpu`
- Или уменьшите batch_size в коде

**Whisper model not found**
- Убедитесь, что модель скачана в `models/whisper/`
- Проверьте наличие `config.json`

**YouTube API errors**
- Проверьте RAPIDAPI_KEY
- Попробуйте VPN

---

## 📄 Лицензия

MIT
