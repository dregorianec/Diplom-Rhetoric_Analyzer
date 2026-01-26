# Миграция на LiteLLM

## Что было сделано

1. ✅ Создан новый клиент `LiteLLMChain` в `src/infrastructure/llm/litellm_client.py`
2. ✅ Обновлена конфигурация в `src/config.py` для поддержки LiteLLM
3. ✅ Обновлен `src/app.py` - заменен `OpenAILLMChain` на `LiteLLMChain` во всех функциях
4. ✅ Добавлен `litellm>=1.0.0` в `requirements.txt`
5. ✅ Обновлен `env.example` с настройками для proxy.merkulov.ai

## Настройка

### 1. Установить зависимости

```bash
pip install -r requirements.txt
```

### 2. Настроить .env файл

Скопируйте `env.example` в `.env` и обновите настройки:

```env
# API ключ для LiteLLM (proxy.merkulov.ai)
# ВАЖНО: Замените на свой реальный ключ!
LLM_API_KEY=your-llm-api-key-here

# Базовый URL для proxy
LLM_API_BASE=https://proxy.merkulov.ai

# Модель через LiteLLM (gpt-4, claude-3-opus, gpt-3.5-turbo, etc.)
LLM_MODEL=gpt-4

# Остальные настройки
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=256
LLM_TIMEOUT_S=120
LLM_USE_LOGPROBS=false
```

### 3. Использование

Система теперь автоматически использует LiteLLM для всех LLM запросов:

```bash
# Полный пайплайн
python -m src.app analyze --politician "Donald Trump"

# Анализ транскрипта
python -m src.app legacy --transcript-path data/transcripts/speech.txt

# Локальный файл
python -m src.app local --file data/videos/video.wav
```

## Доступные модели

Через LiteLLM можно использовать любую из 100+ моделей:

- `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo` (OpenAI)
- `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku` (Anthropic)
- `gemini-pro` (Google)
- И многие другие...

Просто укажите название модели в `LLM_MODEL` в `.env` файле.

## Особенности

- **Proxy поддержка**: Автоматическая работа через proxy.merkulov.ai
- **Logprobs**: Опциональная поддержка logprobs для вычисления confidence (включить через `LLM_USE_LOGPROBS=true`)
- **Обратная совместимость**: Старый `OpenAILLMChain` оставлен в коде, но не используется

## Отладка

Если возникают проблемы:

1. Проверьте подключение к proxy:
   ```bash
   curl https://proxy.merkulov.ai/health
   ```

2. Проверьте логи - все ошибки LiteLLM логируются через стандартный logger

3. Убедитесь, что API ключ правильный и не истек

4. Проверьте, что модель доступна через proxy
