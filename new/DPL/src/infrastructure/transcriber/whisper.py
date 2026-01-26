"""
Whisper Transcriber - локальная транскрибация через whisper-large-v3.
"""
import logging
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from src.domain.interfaces import Transcriber
from src.domain.models import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class WhisperTranscriber(Transcriber):
    """
    Транскрибация аудио/видео через локальную модель Whisper.
    
    Использует Hugging Face Transformers для загрузки и инференса.
    Модель: openai/whisper-large-v3
    """

    def __init__(
        self,
        model_path: str | Path = "openai/whisper-large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "en",
        chunk_length_s: int = 30,
        batch_size: int = 16,
    ):
        """
        Инициализация транскрибера.
        
        Args:
            model_path: Путь к локальной модели или ID на Hugging Face
            device: Устройство для инференса ("cuda" / "cpu")
            compute_type: Тип вычислений ("float16" / "float32" / "int8")
            language: Язык для транскрибации ("en", "ru", None для auto)
            chunk_length_s: Длина чанков для обработки (секунды)
            batch_size: Размер батча
        """
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.chunk_length_s = chunk_length_s
        self.batch_size = batch_size
        
        self._model = None
        self._processor = None
        self._pipe = None

    def _load_model(self):
        """Ленивая загрузка модели."""
        if self._pipe is not None:
            return

        logger.info("Loading Whisper model from: %s", self.model_path)

        # Определяем dtype
        if self.compute_type == "float16":
            torch_dtype = torch.float16
        elif self.compute_type == "int8":
            torch_dtype = torch.int8
        else:
            torch_dtype = torch.float32

        # Определяем устройство
        if self.device == "cuda" and torch.cuda.is_available():
            device = "cuda:0"
        else:
            device = "cpu"
            if self.device == "cuda":
                logger.warning("CUDA not available, falling back to CPU")

        # Загружаем модель
        model_id = str(self.model_path)
        
        self._model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        )
        self._model.to(device)

        self._processor = AutoProcessor.from_pretrained(model_id)

        # Создаём pipeline
        self._pipe = pipeline(
            "automatic-speech-recognition",
            model=self._model,
            tokenizer=self._processor.tokenizer,
            feature_extractor=self._processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device,
            chunk_length_s=self.chunk_length_s,
            batch_size=self.batch_size,
        )

        logger.info("Whisper model loaded successfully on %s", device)

    def transcribe(self, media_path: Path) -> TranscriptResult:
        """
        Транскрибирует аудио/видео файл.
        
        Args:
            media_path: Путь к медиафайлу (.wav, .mp3, .mp4, etc.)
            
        Returns:
            TranscriptResult с текстом и сегментами
        """
        self._load_model()

        if not media_path.exists():
            raise FileNotFoundError(f"Media file not found: {media_path}")

        logger.info("Transcribing: %s", media_path)

        # Параметры генерации
        generate_kwargs = {}
        if self.language and self.language != "auto":
            generate_kwargs["language"] = self.language

        # Запускаем транскрибацию
        result = self._pipe(
            str(media_path),
            return_timestamps=True,
            generate_kwargs=generate_kwargs,
        )

        # Парсим результат
        full_text = result.get("text", "").strip()
        chunks = result.get("chunks", [])

        segments = []
        for chunk in chunks:
            timestamp = chunk.get("timestamp", (0.0, 0.0))
            start = timestamp[0] if timestamp[0] is not None else 0.0
            end = timestamp[1] if timestamp[1] is not None else start
            
            segments.append(TranscriptSegment(
                start=start,
                end=end,
                text=chunk.get("text", "").strip(),
            ))

        # Вычисляем общую длительность
        duration = segments[-1].end if segments else 0.0

        logger.info("Transcription complete: %d segments, %.1f seconds", len(segments), duration)

        return TranscriptResult(
            text=full_text,
            segments=segments,
            language=self.language or "auto",
            duration=duration,
        )

    def transcribe_with_speakers(self, media_path: Path, num_speakers: int = 2) -> TranscriptResult:
        """
        Транскрибация с определением спикеров (diarization).
        
        Примечание: для полноценной диаризации нужен pyannote.audio,
        здесь базовая реализация без диаризации.
        """
        # Базовая транскрибация
        result = self.transcribe(media_path)
        
        # TODO: Добавить pyannote.audio для speaker diarization
        # Пока просто возвращаем результат без разделения по спикерам
        
        return result
