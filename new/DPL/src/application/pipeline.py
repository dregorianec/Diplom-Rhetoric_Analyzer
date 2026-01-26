"""
Unified Pipeline: Search → Download → Transcribe → Analyze → Visualize
"""
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.domain.interfaces import (
    YouTubeSearcher,
    VideoDownloader,
    Transcriber,
    MistakeCatalog,
    Chunker,
    AnalyzerChain,
    ResultWriter,
    TranscriptProvider,
)
from src.domain.models import (
    AnalysisResult,
    VideoSearchResult,
    VideoMetadata,
    TranscriptResult,
)

logger = logging.getLogger(__name__)


class JsonResultWriter(ResultWriter):
    """Записывает результаты анализа в JSON файл."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_prefix(prefix: str) -> str:
        """Делает безопасное имя файла под Windows."""
        safe = re.sub(r'[<>:"/\\|?*]+', "_", prefix)
        safe = safe.replace(" ", "_")
        # ограничим длину чтобы не превышать лимиты пути
        return safe[:120]

    def write(self, results: List[AnalysisResult], prefix: str = "mistakes") -> Path:
        safe_prefix = self._safe_prefix(prefix)
        filename = datetime.now().strftime(f"{safe_prefix}-%Y-%m-%d_%H-%M-%S.json")
        target = self.base_dir / filename
        
        serializable = []
        for r in results:
            serializable.append({
                "group_idx": r.group_idx,
                "speaker_slug": r.speaker_slug,
                "mistake_slug": r.mistake_slug,
                "group_start_char_id": r.group_start_char_id,
                "group_end_char_id": r.group_end_char_id,
                "chunk_start_char_id": r.chunk_start_char_id,
                "chunk_end_char_id": r.chunk_end_char_id,
                "reason": r.reason,
                "how_starts": r.how_starts,
                "how_ends": r.how_ends,
            })
        
        target.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info("Results saved to: %s", target)
        return target


class TranscriptSaver:
    """Сохраняет транскрипты в файлы."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, transcript: TranscriptResult, video_id: str) -> Path:
        """Сохраняет транскрипт в текстовый файл."""
        filename = f"{video_id}.txt"
        target = self.base_dir / filename
        
        # Сохраняем с таймкодами
        content = transcript.to_timestamped_text()
        target.write_text(content, encoding="utf-8")
        
        # Также сохраняем plain text версию
        plain_target = self.base_dir / f"{video_id}_plain.txt"
        plain_target.write_text(transcript.text, encoding="utf-8")
        
        logger.info("Transcript saved to: %s", target)
        return target


class FullPipeline:
    """
    Полный пайплайн: поиск → скачивание → транскрибация → анализ.
    
    Поток данных:
    1. Поиск видео по имени политика
    2. Скачивание видео (аудио)
    3. Транскрибация через Whisper
    4. Разбиение на чанки
    5. LLM анализ каждого чанка на ошибки
    6. Сохранение результатов
    """

    def __init__(
        self,
        searcher: YouTubeSearcher,
        downloader: VideoDownloader,
        transcriber: Transcriber,
        catalog: MistakeCatalog,
        chunker: Chunker,
        analyzer: AnalyzerChain,
        result_writer: ResultWriter,
        transcript_saver: TranscriptSaver,
    ):
        self.searcher = searcher
        self.downloader = downloader
        self.transcriber = transcriber
        self.catalog = catalog
        self.chunker = chunker
        self.analyzer = analyzer
        self.result_writer = result_writer
        self.transcript_saver = transcript_saver

    def run(
        self,
        politician_name: str,
        max_videos: int = 1,
        skip_existing: bool = True,
        max_groups: int | None = None,
        sleep_between_llm_calls_s: float = 0.0,
    ) -> dict:
        """
        Запускает полный пайплайн.
        
        Args:
            politician_name: Имя политика для поиска
            max_videos: Максимальное количество видео для обработки
            skip_existing: Пропускать уже обработанные видео
            
        Returns:
            Словарь с результатами:
            - videos: список обработанных видео
            - results_path: путь к файлу результатов
            - total_mistakes: общее количество найденных ошибок
        """
        logger.info("Starting pipeline for: %s", politician_name)
        
        # 1. Поиск видео
        search_query = f"{politician_name} speech"
        videos = self.searcher.search(search_query, max_results=max_videos)
        
        if not videos:
            logger.warning("No videos found for: %s", politician_name)
            return {"videos": [], "results_path": None, "total_mistakes": 0}
        
        logger.info("Found %d videos", len(videos))
        
        all_results: List[AnalysisResult] = []
        processed_videos: List[dict] = []
        
        for video in videos:
            logger.info("Processing video: %s (%s)", video.title, video.video_id)
            
            try:
                # 2. Скачивание
                metadata = self.downloader.download(video.video_id)
                logger.info("Downloaded: %s", metadata.stored_path)
                
                # 3. Транскрибация
                transcript = self.transcriber.transcribe(Path(metadata.stored_path))
                self.transcript_saver.save(transcript, video.video_id)
                logger.info("Transcribed: %d characters", len(transcript.text))
                
                # 4. Разбиение на чанки
                groups = self.chunker.split(transcript.text)
                logger.info("Created %d chunk groups", len(groups))
                
                # 5. Анализ
                mistakes = self.catalog.list()
                video_results = self._analyze_groups(
                    groups,
                    mistakes,
                    max_groups=max_groups,
                    sleep_between_calls_s=sleep_between_llm_calls_s,
                )
                all_results.extend(video_results)
                
                processed_videos.append({
                    "video_id": video.video_id,
                    "title": video.title,
                    "duration": video.duration,
                    "transcript_length": len(transcript.text),
                    "mistakes_found": len(video_results),
                })
                
            except Exception as e:
                logger.error("Failed to process video %s: %s", video.video_id, e)
                continue
        
        # 6. Сохранение результатов
        # Пишем файл всегда, даже если results пустой — чтобы было понятно, что прогон завершился
        results_path = self.result_writer.write(all_results, prefix=f"analysis-{politician_name.replace(' ', '_')}")
        
        return {
            "politician": politician_name,
            "videos": processed_videos,
            "results_path": str(results_path) if results_path else None,
            "total_mistakes": len(all_results),
        }

    def _analyze_groups(
        self,
        groups,
        mistakes,
        max_groups: int | None = None,
        sleep_between_calls_s: float = 0.0,
    ) -> List[AnalysisResult]:
        """
        Анализирует группы, делая 1 LLM-вызов на группу для всех ошибок сразу.
        """
        results: List[AnalysisResult] = []
        consecutive_errors = 0

        total = len(groups)
        limit = min(total, max_groups) if max_groups is not None else total
        logger.info("LLM analysis groups: %d/%d", limit, total)

        for idx, group in enumerate(groups[:limit]):
            if group.items[-1].speaker == "other":
                continue

            try:
                analysis = self.analyzer.analyze_group(idx, group, mistakes)
                results.extend(analysis)
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                logger.warning("Analysis failed for group %d: %s", idx, e)
                # Если LM Studio упал/502 — остановимся после нескольких подряд ошибок
                if consecutive_errors >= 5:
                    logger.error("Too many consecutive LLM errors (%d). Stopping analysis early.", consecutive_errors)
                    break
            finally:
                if sleep_between_calls_s and sleep_between_calls_s > 0:
                    time.sleep(sleep_between_calls_s)

        return results


class LegacyPipeline:
    """
    Устаревший пайплайн для работы с готовыми транскриптами.
    Совместим с оригинальным app.py.
    """

    def __init__(
        self,
        catalog: MistakeCatalog,
        chunker: Chunker,
        analyzer: AnalyzerChain,
        writer: ResultWriter,
        transcript_provider: TranscriptProvider,
        video_downloader: Optional[VideoDownloader] = None,
    ):
        self.catalog = catalog
        self.chunker = chunker
        self.analyzer = analyzer
        self.writer = writer
        self.transcript_provider = transcript_provider
        self.video_downloader = video_downloader

    def run(
        self,
        transcript_path: Path,
        video_url: Optional[str] = None,
        max_groups: int | None = None,
        sleep_between_llm_calls_s: float = 0.0,
    ) -> Path:
        """Запускает анализ готового транскрипта."""
        if video_url and self.video_downloader:
            self.video_downloader.download(video_url)

        text = self.transcript_provider.load_text(transcript_path)
        groups = self.chunker.split(text)
        mistakes = self.catalog.list()

        results: List[AnalysisResult] = []
        total = len(groups)
        limit = min(total, max_groups) if max_groups is not None else total
        logger.info("Created %d chunk groups (using %d)", total, limit)

        consecutive_errors = 0
        for idx, group in enumerate(groups[:limit]):
            if group.items[-1].speaker == "other":
                continue
            try:
                analysis = self.analyzer.analyze_group(idx, group, mistakes)
                results.extend(analysis)
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                logger.warning("Analysis failed for group %d: %s", idx, e)
                if consecutive_errors >= 5:
                    logger.error("Too many consecutive LLM errors (%d). Stopping early.", consecutive_errors)
                    break
            finally:
                if sleep_between_llm_calls_s and sleep_between_llm_calls_s > 0:
                    time.sleep(sleep_between_llm_calls_s)

        output = self.writer.write(results)
        return output
