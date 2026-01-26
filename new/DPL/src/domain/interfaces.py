from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List

from .models import VideoMetadata, VideoSearchResult, Mistake, ChunkGroup, AnalysisResult, TranscriptResult


class YouTubeSearcher(ABC):
    """Интерфейс для поиска видео на YouTube по запросу."""

    @abstractmethod
    def search(self, query: str, max_results: int = 1) -> List[VideoSearchResult]:
        """
        Ищет видео по запросу.
        
        Args:
            query: Поисковый запрос (например, имя политика)
            max_results: Максимальное количество результатов
            
        Returns:
            Список найденных видео
        """
        ...


class VideoDownloader(ABC):
    """Интерфейс для скачивания видео."""

    @abstractmethod
    def download(self, video_id: str) -> VideoMetadata:
        """
        Скачивает видео по ID.
        
        Args:
            video_id: ID видео на YouTube
            
        Returns:
            Метаданные скачанного видео
        """
        ...


class VideoStorage(ABC):
    """Интерфейс для хранения видеофайлов."""

    @abstractmethod
    def save(self, filename: str, content: bytes) -> Path:
        """Сохраняет файл и возвращает путь."""
        ...

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """Проверяет существование файла."""
        ...

    @abstractmethod
    def get_path(self, filename: str) -> Path:
        """Возвращает путь к файлу."""
        ...


class Transcriber(ABC):
    """Интерфейс для транскрибации аудио/видео в текст."""

    @abstractmethod
    def transcribe(self, media_path: Path) -> TranscriptResult:
        """
        Транскрибирует аудио/видео файл.
        
        Args:
            media_path: Путь к медиафайлу
            
        Returns:
            Результат транскрибации с текстом и сегментами
        """
        ...


class TranscriptProvider(ABC):
    """Интерфейс для загрузки готовых транскриптов из файлов."""

    @abstractmethod
    def load_text(self, path: Path) -> str:
        """Загружает текст транскрипта из файла."""
        ...


class Chunker(ABC):
    """Интерфейс для разбиения текста на чанки."""

    @abstractmethod
    def split(self, text: str) -> List[ChunkGroup]:
        """Разбивает текст на группы чанков со скользящим окном."""
        ...


class MistakeCatalog(ABC):
    """Интерфейс для каталога риторических ошибок."""

    @abstractmethod
    def list(self) -> List[Mistake]:
        """Возвращает список всех ошибок для анализа."""
        ...


class AnalyzerChain(ABC):
    """Интерфейс для LLM-анализа чанков."""

    @abstractmethod
    def analyze_group(self, group_idx: int, group: ChunkGroup, mistakes: List[Mistake]) -> List[AnalysisResult]:
        """
        Анализирует группу чанков на наличие ошибок (список).
        
        Args:
            group_idx: Индекс группы
            group: Группа чанков (окно контекста)
            mistakes: Список ошибок для поиска
            
        Returns:
            Список найденных ошибок
        """
        ...


class ResultWriter(ABC):
    """Интерфейс для записи результатов анализа."""

    @abstractmethod
    def write(self, results: Iterable[AnalysisResult]) -> Path:
        """Записывает результаты и возвращает путь к файлу."""
        ...


class Visualizer(ABC):
    """Интерфейс для визуализации результатов."""

    @abstractmethod
    def plot_mistakes_by_speaker(self, results: List[AnalysisResult], output_path: Path | None = None) -> None:
        """Строит график ошибок по спикерам."""
        ...

    @abstractmethod
    def plot_mistakes_distribution(self, results: List[AnalysisResult], output_path: Path | None = None) -> None:
        """Строит график распределения типов ошибок."""
        ...
