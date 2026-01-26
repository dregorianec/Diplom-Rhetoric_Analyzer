"""
YouTube Video Downloader через yt-dlp.
"""
import logging
from pathlib import Path

import yt_dlp

from src.domain.interfaces import VideoDownloader, VideoStorage
from src.domain.models import VideoMetadata

logger = logging.getLogger(__name__)


class YtDlpDownloader(VideoDownloader):
    """
    Скачивание видео с YouTube через yt-dlp.
    Сохраняет аудио в формате wav для транскрибации.
    """

    def __init__(
        self,
        storage: VideoStorage,
        audio_format: str = "wav",
        audio_quality: str = "192",
    ):
        self.storage = storage
        self.audio_format = audio_format
        self.audio_quality = audio_quality

    def download(self, video_id: str) -> VideoMetadata:
        """
        Скачивает видео и извлекает аудио.
        
        Args:
            video_id: ID видео на YouTube
            
        Returns:
            VideoMetadata с путём к скачанному файлу
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_dir = self.storage.get_path("")
        output_template = str(output_dir / video_id)

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.audio_format,
                "preferredquality": self.audio_quality,
            }],
            "outtmpl": output_template,
            "quiet": False,
            "no_warnings": False,
        }

        logger.info("Downloading video: %s", url)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)

            # Путь к скачанному аудио
            audio_path = output_dir / f"{video_id}.{self.audio_format}"

            if not audio_path.exists():
                # Иногда yt-dlp сохраняет с другим расширением
                possible_paths = list(output_dir.glob(f"{video_id}.*"))
                audio_paths = [p for p in possible_paths if p.suffix in [".wav", ".mp3", ".m4a", ".webm", ".opus"]]
                if audio_paths:
                    audio_path = audio_paths[0]
                else:
                    raise FileNotFoundError(f"Downloaded audio not found for {video_id}")

            logger.info("Downloaded: %s -> %s", title, audio_path)

            return VideoMetadata(
                source_url=url,
                stored_path=str(audio_path),
                provider="yt-dlp",
                video_id=video_id,
                title=title,
                duration=duration,
            )

        except Exception as e:
            logger.error("Failed to download %s: %s", video_id, e)
            raise RuntimeError(f"Failed to download video {video_id}: {e}") from e
