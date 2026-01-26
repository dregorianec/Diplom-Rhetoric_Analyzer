import logging
from typing import Optional

import requests

from src.domain.interfaces import VideoDownloader, VideoStorage
from src.domain.models import VideoMetadata

logger = logging.getLogger(__name__)


class ApifyDownloader(VideoDownloader):
    """
    Пример адаптера для Apify actor, который возвращает downloadUrl.
    Требует APIFY_TOKEN и actor_id (можно использовать публичный free-tier actor для YouTube).
    """

    def __init__(self, token: str, actor_id: str, storage: VideoStorage):
        self.token = token
        self.actor_id = actor_id
        self.storage = storage

    def download(self, url: str) -> VideoMetadata:
        start_url = f"https://api.apify.com/v2/acts/{self.actor_id}/run-sync-get-dataset-items"
        params = {"token": self.token, "url": url}
        resp = requests.get(start_url, params=params, timeout=60)
        resp.raise_for_status()
        items = resp.json()
        if not items:
            raise ValueError("Apify response is empty")

        item = items[0]
        download_url: Optional[str] = item.get("downloadUrl") or item.get("url")
        title = item.get("title", "video")
        if not download_url:
            raise ValueError("Apify item does not contain downloadUrl")

        file_resp = requests.get(download_url, timeout=120)
        file_resp.raise_for_status()

        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        filename = f"{safe_title or 'video'}.mp4"
        stored_path = self.storage.save(filename, file_resp.content)

        logger.info("Downloaded video via Apify: %s -> %s", url, stored_path)
        return VideoMetadata(source_url=url, stored_path=str(stored_path), provider="apify")
