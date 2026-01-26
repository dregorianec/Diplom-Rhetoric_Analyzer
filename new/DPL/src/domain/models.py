from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Example:
    """Пример для few-shot prompting."""
    text: str
    result: str


@dataclass
class Mistake:
    """Риторическая ошибка/уловка для детекции."""
    slug: str
    description: str
    examples_positive: Optional[List[Example]] = None
    examples_negative: Optional[List[Example]] = None


@dataclass
class Chunk:
    """Отдельный фрагмент текста."""
    speaker: str
    text: str
    token_length: int
    start_char_id: int
    end_char_id: int


@dataclass
class ChunkGroup:
    """Группа чанков (скользящее окно контекста)."""
    items: List[Chunk]


@dataclass
class MistakeResult:
    """Результат от LLM по одной найденной ошибке."""
    reason: str
    how_starts: str = ""
    how_ends: str = ""


@dataclass
class AnalysisResult:
    """Полный результат анализа одной ошибки в группе."""
    group_idx: int
    speaker_slug: str
    mistake_slug: str
    group_start_char_id: int
    group_end_char_id: int
    chunk_start_char_id: int
    chunk_end_char_id: int
    reason: str
    how_starts: str = ""
    how_ends: str = ""


@dataclass
class VideoMetadata:
    """Метаданные скачанного видео."""
    source_url: str
    stored_path: str
    provider: str
    video_id: str = ""
    title: str = ""
    duration: int = 0  # seconds


@dataclass
class VideoSearchResult:
    """Результат поиска видео на YouTube."""
    video_id: str
    title: str
    channel: str
    duration: int  # seconds
    view_count: int = 0
    thumbnail_url: str = ""
    description: str = ""

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


@dataclass
class TranscriptSegment:
    """Сегмент транскрипции с таймкодами."""
    start: float  # seconds
    end: float
    text: str
    confidence: float = 1.0


@dataclass
class TranscriptResult:
    """Результат транскрибации."""
    text: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: str = "en"
    duration: float = 0.0

    def to_plain_text(self) -> str:
        """Возвращает только текст без таймкодов."""
        return self.text

    def to_timestamped_text(self) -> str:
        """Возвращает текст с таймкодами."""
        lines = []
        for seg in self.segments:
            timestamp = f"[{seg.start:.1f}s - {seg.end:.1f}s]"
            lines.append(f"{timestamp} {seg.text}")
        return "\n".join(lines)