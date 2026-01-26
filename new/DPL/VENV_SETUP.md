# Запуск и тестирование через venv

## 🚀 Быстрый старт

### 1. Активация виртуального окружения

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

После активации в начале строки появится `(venv)`.

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

Если venv уже был создан ранее, обновите зависимости:
```bash
pip install --upgrade -r requirements.txt
```

### 3. Настройка .env файла

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

Отредактируйте `.env` файл и укажите свои ключи:
```env
LLM_API_KEY=your-llm-api-key-here
LLM_API_BASE=https://proxy.merkulov.ai
LLM_MODEL=gpt-4
```

---

## 🧪 Тестирование

### Тест 1: Проверка подключения к LiteLLM

Создайте простой тестовый скрипт `test_litellm.py`:

```python
import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

response = completion(
    model=os.getenv("LLM_MODEL", "gpt-4"),
    messages=[{"role": "user", "content": "Say 'Hello from LiteLLM!'"}],
    api_key=os.getenv("LLM_API_KEY"),
    api_base=os.getenv("LLM_API_BASE"),
)

print("Response:", response.choices[0].message.content)
print("✅ LiteLLM работает!")
```

Запустите:
```bash
python test_litellm.py
```

### Тест 2: Проверка конфигурации

```bash
python -c "from src.config import get_settings; s = get_settings(); print(f'Model: {s.llm_model}'); print(f'API Base: {s.llm_api_base}'); print(f'API Key: {s.llm_api_key[:10]}...')"
```

### Тест 3: Анализ готового транскрипта (быстрый тест)

Если у вас есть транскрипт в `data/transcripts/`:

```bash
python -m src.app legacy --transcript-path data/transcripts/za9___oByoA_plain.txt --no-plot
```

### Тест 4: Полный пайплайн (долгий)

```bash
# Анализ одного видео
python -m src.app analyze --politician "Donald Trump" --max-videos 1 --no-plot

# С расширенным каталогом
python -m src.app analyze --politician "Donald Trump" --extended --no-plot
```

---

## 📋 Основные команды

### Анализ политика (полный пайплайн)
```bash
python -m src.app analyze --politician "Donald Trump"
```

Опции:
- `--max-videos N` - количество видео (по умолчанию 1)
- `--extended` - расширенный каталог ошибок (15 типов)
- `--no-plot` - не показывать графики
- `--save-plot-only` - только сохранить графики

### Анализ готового транскрипта
```bash
python -m src.app legacy --transcript-path data/transcripts/speech.txt
```

### Анализ локального аудио/видео файла
```bash
python -m src.app local --file data/videos/video.wav
```

### Визуализация результатов
```bash
python -m src.app visualize --results-file data/results/analysis-2024-01-01.json
```

---

## 🔍 Отладка

### Проверка установленных пакетов
```bash
pip list | grep -E "litellm|langchain|torch"
```

### Проверка импортов
```bash
python -c "from src.infrastructure.llm.litellm_client import LiteLLMChain; print('✅ Импорт успешен')"
```

### Логирование
Все логи выводятся в консоль. Для более детального логирования можно изменить уровень в `src/app.py`:

```python
logging.basicConfig(level=logging.DEBUG)  # вместо INFO
```

### Типичные ошибки

**1. ModuleNotFoundError: No module named 'litellm'**
```bash
pip install litellm
```

**2. API key error**
- Проверьте `.env` файл
- Убедитесь, что ключ правильный и не истек

**3. Connection error к proxy**
- Проверьте интернет соединение
- Проверьте, что `LLM_API_BASE=https://proxy.merkulov.ai` в `.env`

**4. Model not found**
- Попробуйте другую модель: `gpt-3.5-turbo` или `claude-3-haiku`
- Проверьте доступность модели через proxy

---

## 🛑 Деактивация venv

После работы:

```bash
deactivate
```

---

## 📝 Примеры использования

### Быстрый тест на коротком транскрипте

1. Создайте тестовый файл `test_transcript.txt`:
```
This is a test speech. I think my opponent is wrong because they are stupid.
```

2. Запустите анализ:
```bash
python -m src.app legacy --transcript-path test_transcript.txt --no-plot
```

### Тест с разными моделями

Измените в `.env`:
```env
LLM_MODEL=gpt-3.5-turbo  # быстрее и дешевле
# или
LLM_MODEL=claude-3-haiku  # альтернатива
```

Затем запустите:
```bash
python -m src.app legacy --transcript-path data/transcripts/za9___oByoA_plain.txt --no-plot
```

---

## ✅ Чеклист перед первым запуском

- [ ] venv активирован (видно `(venv)` в начале строки)
- [ ] Установлены зависимости: `pip install -r requirements.txt`
- [ ] Создан `.env` файл из `env.example`
- [ ] Проверен API ключ в `.env`
- [ ] Модель Whisper установлена (если нужна транскрипция)
- [ ] Протестировано подключение к LiteLLM

---

## 🎯 Рекомендуемый порядок тестирования

1. **Тест LiteLLM** (30 сек)
   ```bash
   python test_litellm.py
   ```

2. **Тест конфигурации** (5 сек)
   ```bash
   python -c "from src.config import get_settings; print(get_settings().llm_model)"
   ```

3. **Тест анализа транскрипта** (1-2 мин)
   ```bash
   python -m src.app legacy --transcript-path data/transcripts/za9___oByoA_plain.txt --no-plot
   ```

4. **Полный пайплайн** (10-30 мин)
   ```bash
   python -m src.app analyze --politician "Donald Trump" --max-videos 1 --no-plot
   ```
