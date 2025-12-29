# Название (фиксированное)

**Разработка микросервисной платформы на основе LLM-агентов для сбора, обработки и семантического анализа медиаконтента**

---

# Краткое описание (1–3 предложения)

В работе разрабатывается микросервисная платформа для автоматизированного сбора видеоконтента (YouTube), преобразования аудио в текст и последующего семантического анализа с использованием локальных LLM-агентов и retrieval-подсистемы. Система ориентирована на production-эксплуатацию: микросервисы, очереди задач, контейнеризация, мониторинг и audit-trail; особое внимание уделено объяснимому анализу и возможностям human-in-the-loop. Эксперименты включают оценку качества транскрипции, точности детекции риторических/семантических паттернов и устойчивости пайплайна под нагрузкой.

---

# Практическая ценность (чётко и по делу)

* Конвертация медиаконтента в структурированные инсайты — востребовано в СМИ, fact-checking, НКО и PR.
* Production-готовый pipeline снимает барьер внедрения (масштабируемость, наблюдаемость, audit).
* Демонстрирует навыки MLOps + ML engineering + системной инженерии, ценимые на рабочих должностях.

---

# Краткий технологический стек (по-деловому)

* Язык:  **Python 3.11** ; API:  **FastAPI** ; схемы: **Pydantic**
* ASR: **whisper.cpp / локальная Whisper**
* LLM-агенты: **llama.cpp + GGUF (малые 1–7B)** для rationale/объяснений и planner-тасков
* Embeddings + RAG: **sentence-transformers (mini)** + **FAISS**
* Оркестрация: **Celery** + **Redis**
* Хранение: **PostgreSQL** (метаданные, аудит), объектное хранилище для медиа
* Контейнеризация: **Docker** +  **docker-compose** ; мониторинг: **Prometheus/Grafana**
* Тестирование:  **pytest** , нагрузка: **Locust**

---

# MVP-план реализации (коротко, по порядку)

0. **Архитектурная фиксация** : Pydantic контракты, health-endpoints, docker-compose (postgres, redis, api, orchestrator).
1. **Ingest + Transcribe** : YouTube → audio → whisper → timestamped текст (отдельный сервис).
2. **Orchestrator + Workers** : Celery pipeline: ingest → transcribe → analyze; обеспечить retry, idempotence.
3. **Rule-based анализ** : быстрый слой детекции семантических/риторических паттернов (regex, lexica).
4. **RAG + ML-классификатор** : FAISS retrieval, fine-tune lightweight classifier (DistilBERT/MiniLM) для ключевых классов; объяснения через локальный LLM.
5. **UI + Audit** : Streamlit/React dashboard с timeline, explainability, human-in-loop для эскалации; логирование всех шагов.
6. **Production hardening** : structured logs, metrics, load/chaos tests, контейнеризация всех сервисов.

---

# Ключевые метрики для оценки

* ASR: WER на тестовой выборке.
* Анализ: precision/recall/F1 по обнаружению целевых семантических/риторических классов.
* Latency: median / 95th percentile от появления видео до публикации результата.
* Robustness: % успешных задач при одновременной нагрузке N.
* Explainability: human rating полезности объяснений (1–5).

---

# Основные артефакты к защите

* GitHub репозиторий с docker-compose и кодом сервисов.
* E2E demo (запись или live): YouTube → транскрипция → анализ → dashboard.
* Evaluation report с метриками и сравнением rule vs ML.
* Audit-логи и примеры human-in-loop решений.

---

# Короткая строка для резюме

«Разработал микросервисную платформу для автоматического сбора YouTube-видео, ASR, RAG-поддержанного семантического анализа и explainable-аналитики на базе локальных LLM; стек: Python, Whisper, FAISS, llama.cpp, Celery, Docker.»
