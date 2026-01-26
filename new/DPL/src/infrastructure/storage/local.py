from pathlib import Path
from src.domain.interfaces import VideoStorage


class LocalVideoStorage(VideoStorage):
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> Path:
        target = self.base_dir / filename
        target.write_bytes(content)
        return target

    def exists(self, filename: str) -> bool:
        return (self.base_dir / filename).exists()

    def get_path(self, filename: str) -> Path:
        """Возвращает путь к файлу (или базовую директорию если filename пустой)."""
        if not filename:
            return self.base_dir
        return self.base_dir / filename