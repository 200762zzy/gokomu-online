import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MatchEntry:
    user_id: int
    username: str
    elo: int
    ws_id: int
    joined_at: float


class Matchmaker:
    def __init__(self):
        self._queue: dict[int, MatchEntry] = {}
        self._lock = asyncio.Lock()

    async def add_to_queue(self, entry: MatchEntry) -> tuple[bool, Optional[MatchEntry]]:
        """Returns (matched, other_entry). If matched, both entries are removed from queue."""
        async with self._lock:
            if entry.ws_id in self._queue:
                return False, None
            self._queue[entry.ws_id] = entry

            # Try to find a match
            for ws_id, existing in list(self._queue.items()):
                if ws_id == entry.ws_id:
                    continue
                elo_diff = abs(existing.elo - entry.elo)
                wait_time = asyncio.get_event_loop().time() - min(existing.joined_at, entry.joined_at)
                max_diff = 100 + int(wait_time / 10) * 50
                if elo_diff <= max_diff:
                    # Match found — remove both from queue
                    del self._queue[ws_id]
                    del self._queue[entry.ws_id]
                    return True, existing
            return False, None

    async def remove_from_queue(self, ws_id: int):
        async with self._lock:
            self._queue.pop(ws_id, None)

    def is_in_queue(self, ws_id: int) -> bool:
        return ws_id in self._queue

    @property
    def queue_size(self) -> int:
        return len(self._queue)


matchmaker = Matchmaker()
