from collections import deque
from typing import List, Dict, Callable

import tiktoken

from src.domain.interfaces import Chunker
from src.domain.models import Chunk, ChunkGroup


class SlidingWindowChunker(Chunker):
    """
    Универсальный чанкер со скользящим окном.
    split_fn: функция разделения на сырые фрагменты.
    speaker_fn: функция определения спикера по фрагменту.
    """

    def __init__(
        self,
        max_tokens: int = 6000,
        max_chunks: int = 12,
        window_start: int = 6,
        split_fn: Callable[[str], List[str]] | None = None,
        speaker_fn: Callable[[str], str] | None = None,
    ):
        self.max_tokens = max_tokens
        self.max_chunks = max_chunks
        self.window_start = window_start
        self.split_fn = split_fn or self._split_by_double_newline
        self.speaker_fn = speaker_fn or (lambda chunk: "other")
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def split(self, text: str) -> List[ChunkGroup]:
        raw_chunks = self.split_fn(text)
        positions: List[tuple[int, int]] = []
        speakers: List[str] = []

        current_pos = 0
        for chunk in raw_chunks:
            speaker = self.speaker_fn(chunk)
            start_pos = current_pos
            end_pos = current_pos + len(chunk)
            positions.append((start_pos, end_pos))
            speakers.append(speaker)
            # добавляем разделитель длиной split marker (для double newline — 2 символа)
            current_pos = end_pos + 2

        chunk_objs: List[Chunk] = []
        for chunk, pos, speaker in zip(raw_chunks, positions, speakers):
            token_len = len(self.tokenizer.encode(chunk))
            chunk_objs.append(
                Chunk(
                    speaker=speaker,
                    text=chunk,
                    token_length=token_len,
                    start_char_id=pos[0],
                    end_char_id=pos[1],
                )
            )

        return self._combine_to_groups(chunk_objs)

    def _combine_to_groups(self, chunk_objs: List[Chunk]) -> List[ChunkGroup]:
        groups: List[ChunkGroup] = []
        start_idx = self.window_start
        curr_grp: deque[Chunk] = deque(chunk_objs[:start_idx])
        curr_sum = sum(c.token_length for c in curr_grp)

        for i in range(start_idx, len(chunk_objs)):
            curr_sum += chunk_objs[i].token_length
            while curr_sum > self.max_tokens or len(curr_grp) > self.max_chunks - 1:
                curr_sum -= curr_grp.popleft().token_length
            curr_grp.append(chunk_objs[i])
            groups.append(ChunkGroup(items=list(curr_grp)))
        return groups

    @staticmethod
    def _split_by_double_newline(text: str) -> List[str]:
        return text.split("\n\n")
