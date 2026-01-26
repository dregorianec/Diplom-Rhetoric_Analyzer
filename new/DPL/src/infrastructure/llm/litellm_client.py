from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

import litellm
from litellm import completion

from src.domain.interfaces import AnalyzerChain
from src.domain.models import Mistake, ChunkGroup, AnalysisResult

logger = logging.getLogger(__name__)


class LiteLLMChain(AnalyzerChain):
    """
    LLM-цепочка через LiteLLM: анализирует только последний чанк окна.
    
    Использует LiteLLM для доступа к различным LLM через единый интерфейс.
    Поддерживает proxy.merkulov.ai для маршрутизации запросов.
    """

    SYSTEM_PROMPT = (
        "You are an expert in rhetorical analysis. "
        "You will be given a text window and a list of rhetorical fallacies. "
        "Identify fallacies ONLY in the FINAL PART of the text. "
        "Be strict, avoid false positives. "
        "Return ONLY valid JSON in this format:\n"
        "{\n"
        "  \"detections\": [\n"
        "    {\n"
        "      \"mistake_slug\": \"...\",\n"
        "      \"reason\": \"...\",\n"
        "      \"how_starts\": \"...\",\n"
        "      \"how_ends\": \"...\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "If no fallacies are found, return {\"detections\": []}.\n"
    )

    def __init__(
        self,
        model: str,
        api_key: str,
        api_base: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 256,
        timeout: float = 120.0,
        use_logprobs: bool = False,
    ):
        """
        Инициализация LiteLLM клиента.
        
        Args:
            model: Название модели (например, "gpt-4", "claude-3-opus")
            api_key: API ключ для LiteLLM
            api_base: Базовый URL для proxy (например, "https://proxy.merkulov.ai")
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов в ответе
            timeout: Таймаут запроса в секундах
            use_logprobs: Использовать logprobs для вычисления confidence
        """
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.use_logprobs = use_logprobs
        
        # Настройка LiteLLM
        if api_key:
            litellm.api_key = api_key
        if api_base:
            litellm.api_base = api_base
        
        # Настройка таймаута
        litellm.request_timeout = timeout

    def _transform_text(self, group: ChunkGroup) -> str:
        """Преобразует группу чанков в текст для анализа."""
        head = "\n".join(c.text for c in group.items[:-1])
        last = group.items[-1].text
        if head:
            return f"{head}\n///Final part to analyse///\n{last}"
        return f"///Final part to analyse///\n{last}"

    def analyze_group(self, group_idx: int, group: ChunkGroup, mistakes: List[Mistake]) -> List[AnalysisResult]:
        """
        Анализирует группу чанков на наличие ошибок.
        
        Args:
            group_idx: Индекс группы
            group: Группа чанков (окно контекста)
            mistakes: Список ошибок для поиска
            
        Returns:
            Список найденных ошибок
        """
        debate_text = self._transform_text(group)
        mistakes_list = "\n".join([f"- {m.slug}: {m.description}" for m in mistakes])

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Fallacies to check:\n{mistakes_list}\n\n"
                    f"Text to analyze:\n{debate_text}\n"
                )
            },
        ]

        # Параметры запроса
        completion_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # Передаем api_key и api_base напрямую в completion для работы с proxy
        if self.api_key:
            completion_kwargs["api_key"] = self.api_key
        if self.api_base:
            completion_kwargs["api_base"] = self.api_base
        
        # Добавляем logprobs если нужно
        if self.use_logprobs:
            completion_kwargs["logprobs"] = True
            completion_kwargs["top_logprobs"] = 5

        try:
            response = completion(**completion_kwargs)
            
            # Извлекаем текст ответа
            if hasattr(response, 'choices') and len(response.choices) > 0:
                raw = response.choices[0].message.content
            else:
                # Fallback для других форматов ответа
                raw = str(response)
            
            detections = self._parse_json(raw)
            
            # Извлекаем logprobs если есть
            logprobs_data = None
            if self.use_logprobs and hasattr(response, 'choices'):
                choice = response.choices[0]
                if hasattr(choice, 'logprobs') and choice.logprobs:
                    logprobs_data = choice.logprobs

            results: List[AnalysisResult] = []
            for det in detections:
                mistake_slug = str(det.get("mistake_slug", "")).strip()
                if not mistake_slug:
                    continue
                
                # Вычисляем confidence из logprobs если доступно
                confidence = self._calculate_confidence(logprobs_data, mistake_slug) if logprobs_data else None
                
                results.append(
                    AnalysisResult(
                        group_idx=group_idx,
                        mistake_slug=mistake_slug,
                        speaker_slug=group.items[-1].speaker,
                        group_start_char_id=group.items[0].start_char_id,
                        group_end_char_id=group.items[-1].end_char_id,
                        chunk_start_char_id=group.items[-1].start_char_id,
                        chunk_end_char_id=group.items[-1].end_char_id,
                        reason=str(det.get("reason", "")).strip(),
                        how_starts=str(det.get("how_starts", "") or ""),
                        how_ends=str(det.get("how_ends", "") or ""),
                    )
                )
            
            return results
            
        except Exception as e:
            logger.error(f"LiteLLM completion failed: {e}")
            raise RuntimeError(f"LLM analysis failed: {e}") from e

    def _parse_json(self, raw: str) -> List[Dict[str, Any]]:
        """
        Парсит JSON ответ от LLM.
        
        Ожидаем JSON: {"detections":[{...}]}
        Иногда модель может вернуть список напрямую — поддержим и это.
        """
        try:
            # Пытаемся найти JSON в тексте (на случай если есть markdown код блоки)
            if "```json" in raw:
                start = raw.find("```json") + 7
                end = raw.find("```", start)
                raw = raw[start:end].strip()
            elif "```" in raw:
                start = raw.find("```") + 3
                end = raw.find("```", start)
                raw = raw[start:end].strip()
            
            data = json.loads(raw)
            if isinstance(data, dict):
                items = data.get("detections", [])
                return items if isinstance(items, list) else []
            if isinstance(data, list):
                return data
            return []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}\nRaw response: {raw[:200]}")
            return []
        except Exception as e:
            logger.warning(f"Unexpected error parsing JSON: {e}")
            return []

    def _calculate_confidence(self, logprobs_data: Any, mistake_slug: str) -> float | None:
        """
        Вычисляет confidence score из logprobs.
        
        Args:
            logprobs_data: Данные logprobs из ответа
            mistake_slug: Название найденной ошибки
            
        Returns:
            Confidence score от 0.0 до 1.0 или None
        """
        if not logprobs_data:
            return None
        
        try:
            # Упрощенная логика: ищем токены связанные с mistake_slug
            # В реальности нужно более сложная обработка logprobs
            # Пока возвращаем None, можно доработать позже
            return None
        except Exception:
            return None
