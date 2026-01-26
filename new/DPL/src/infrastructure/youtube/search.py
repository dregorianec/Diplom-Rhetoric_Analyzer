"""
YouTube Search - поиск видео через разные провайдеры.
"""
import logging
from typing import List

import requests
import yt_dlp

from src.domain.interfaces import YouTubeSearcher
from src.domain.models import VideoSearchResult

logger = logging.getLogger(__name__)


class YtDlpSearcher(YouTubeSearcher):
    """
    Поиск видео через yt-dlp (без API ключей).
    Работает напрямую с YouTube.
    """

    def search(self, query: str, max_results: int = 1) -> List[VideoSearchResult]:
        """
        Ищет видео по запросу через yt-dlp.
        """
        logger.info("Searching YouTube via yt-dlp for: %s", query)

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Не скачивать, только метаданные
            'default_search': 'ytsearch',  # Поиск на YouTube
        }

        # Ищем с запасом, потом фильтруем live и обрезаем
        search_query = f"ytsearch{max_results * 3}:{query}"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(search_query, download=False)

            if not result or 'entries' not in result:
                logger.warning("No results found for: %s", query)
                return []

            entries = result['entries'] or []

            # Сначала фильтруем live/upcoming
            filtered = []
            for entry in entries:
                if not entry:
                    continue
                live_status = entry.get("live_status") or entry.get("was_live")
                if live_status and live_status != "not_live":
                    continue
                filtered.append(entry)

            # Если после фильтра ничего не осталось — используем оригинальные (включая live)
            final_entries = filtered if filtered else entries

            videos = []
            for entry in final_entries:
                video_id = entry.get('id', '')
                if not video_id:
                    continue

                videos.append(VideoSearchResult(
                    video_id=video_id,
                    title=entry.get('title', 'Unknown'),
                    channel=entry.get('channel', entry.get('uploader', 'Unknown')),
                    duration=entry.get('duration', 0) or 0,
                    view_count=entry.get('view_count', 0) or 0,
                    thumbnail_url=entry.get('thumbnail', ''),
                    description=entry.get('description', '') or '',
                ))

            logger.info("Found %d videos for: %s", len(videos), query)
            return videos[:max_results]

        except Exception as e:
            logger.error("yt-dlp search failed: %s", e)
            raise RuntimeError(f"YouTube search failed: {e}") from e


class RapidAPIYouTubeSearcher(YouTubeSearcher):
    """
    Поиск видео на YouTube через RapidAPI youtube138.
    Требует API ключ.
    """

    def __init__(self, api_key: str, api_host: str = "youtube138.p.rapidapi.com"):
        self.api_key = api_key
        self.api_host = api_host
        self.search_endpoint = f"https://{api_host}/search/"

    def search(self, query: str, max_results: int = 1) -> List[VideoSearchResult]:
        """
        Ищет видео по запросу через RapidAPI.
        """
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host,
        }
        params = {
            "q": query,
            "hl": "en",
            "gl": "US",
        }

        try:
            logger.info("Searching YouTube via RapidAPI for: %s", query)
            response = requests.get(
                self.search_endpoint,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("RapidAPI search failed: %s", e)
            raise RuntimeError(f"YouTube search failed: {e}") from e

        results: List[VideoSearchResult] = []
        contents = data.get("contents", [])

        for item in contents:
            video_data = item.get("video", {})
            if not video_data:
                continue

            video_id = video_data.get("videoId", "")
            if not video_id:
                continue

            duration_str = video_data.get("lengthText", "0:00")
            duration = self._parse_duration(duration_str)

            view_count_str = video_data.get("viewCountText", "0")
            view_count = self._parse_view_count(view_count_str)

            results.append(VideoSearchResult(
                video_id=video_id,
                title=video_data.get("title", "Unknown"),
                channel=video_data.get("channelName", "Unknown"),
                duration=duration,
                view_count=view_count,
                thumbnail_url=self._get_thumbnail(video_data),
                description=video_data.get("descriptionSnippet", ""),
            ))

            if len(results) >= max_results:
                break

        logger.info("Found %d videos via RapidAPI", len(results))
        return results

    def _parse_duration(self, duration_str: str) -> int:
        try:
            parts = duration_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except (ValueError, IndexError):
            pass
        return 0

    def _parse_view_count(self, view_str: str) -> int:
        try:
            clean = view_str.lower().replace(",", "").replace(" views", "").replace(" view", "").strip()
            if "k" in clean:
                return int(float(clean.replace("k", "")) * 1000)
            if "m" in clean:
                return int(float(clean.replace("m", "")) * 1_000_000)
            if "b" in clean:
                return int(float(clean.replace("b", "")) * 1_000_000_000)
            return int(clean)
        except (ValueError, AttributeError):
            return 0

    def _get_thumbnail(self, video_data: dict) -> str:
        thumbnails = video_data.get("thumbnails", [])
        if thumbnails and isinstance(thumbnails, list):
            return thumbnails[0].get("url", "")
        return ""
