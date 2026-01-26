from __future__ import annotations

import json
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.domain.interfaces import AnalyzerChain
from src.domain.models import Mistake, ChunkGroup, AnalysisResult


class OpenAILLMChain(AnalyzerChain):
    """
    LLM-цепочка: анализирует только последний чанк окна.

    Важно: делаем ОДИН запрос на окно и просим проверить СРАЗУ все ошибки.
    Это снижает нагрузку на LM Studio и уменьшает шанс 502.
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

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def _transform_text(self, group: ChunkGroup) -> str:
        head = "\n".join(c.text for c in group.items[:-1])
        last = group.items[-1].text
        if head:
            return f"{head}\n///Final part to analyse///\n{last}"
        return f"///Final part to analyse///\n{last}"

    def analyze_group(self, group_idx: int, group: ChunkGroup, mistakes: List[Mistake]) -> List[AnalysisResult]:
        debate_text = self._transform_text(group)
        mistakes_list = "\n".join([f"- {m.slug}: {m.description}" for m in mistakes])

        prompt = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Fallacies to check:\n{mistakes_list}\n\n"
                    f"Text to analyze:\n{debate_text}\n"
                )
            ),
        ]

        raw = self.llm.invoke(prompt).content
        detections = self._parse_json(raw)

        results: List[AnalysisResult] = []
        for det in detections:
            mistake_slug = str(det.get("mistake_slug", "")).strip()
            if not mistake_slug:
                continue
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

    def _parse_json(self, raw: str) -> List[Dict[str, Any]]:
        """
        Ожидаем JSON: {"detections":[{...}]}
        Иногда модель может вернуть список напрямую — поддержим и это.
        """
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                items = data.get("detections", [])
                return items if isinstance(items, list) else []
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []
