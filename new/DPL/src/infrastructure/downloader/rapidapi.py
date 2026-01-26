import logging
from pathlib import Path
from typing import Optional

import requests

from src.domain.interfaces import VideoDownloader, VideoStorage
from src.domain.models import VideoMetadata

logger = logging.getLogger(__name__)


class RapidAPIDownloader(VideoDownloader):
    """
    Пример адаптера под RapidAPI (например youtube-mp36).
    Ожидает endpoint, host и ключ. Работает в free-tier, но ограничен лимитами.
    """

    def __init__(
        self,
        api_key: str,
        api_host: str,
        endpoint: str,
        storage: VideoStorage,
    ):
        self.api_key = api_key
        self.api_host = api_host
        self.endpoint = endpoint
        self.storage = storage

    def download(self, url: str) -> VideoMetadata:
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host,
        }
        params = {"id": url}

        resp = requests.get(self.endpoint, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        download_url: Optional[str] = data.get("link") or data.get("url")
        title = data.get("title", "video")
        if not download_url:
            raise ValueError("RapidAPI response does not contain download link")

        file_resp = requests.get(download_url, timeout=60)
        file_resp.raise_for_status()

        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        filename = f"{safe_title or 'video'}.mp4"
        stored_path = self.storage.save(filename, file_resp.content)

        logger.info("Downloaded video via RapidAPI: %s -> %s", url, stored_path)
        return VideoMetadata(source_url=url, stored_path=str(stored_path), provider="rapidapi")
