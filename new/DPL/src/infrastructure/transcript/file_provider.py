from pathlib import Path
from src.domain.interfaces import TranscriptProvider


class FileTranscriptProvider(TranscriptProvider):
    def load_text(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_text(encoding="utf-8")
