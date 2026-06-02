import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    from_user: str
    from_user_id: int
    message: str
    room_id: str = ""


class ChatManager:
    def __init__(self):
        self._global_history: list[ChatMessage] = []
        self._room_history: dict[str, list[ChatMessage]] = {}

    def add_global_message(self, msg: ChatMessage):
        self._global_history.append(msg)
        if len(self._global_history) > 200:
            self._global_history = self._global_history[-200:]

    def add_room_message(self, room_id: str, msg: ChatMessage):
        if room_id not in self._room_history:
            self._room_history[room_id] = []
        self._room_history[room_id].append(msg)
        if len(self._room_history[room_id]) > 100:
            self._room_history[room_id] = self._room_history[room_id][-100:]

    def get_global_history(self, limit: int = 50) -> list[ChatMessage]:
        return self._global_history[-limit:]

    def get_room_history(self, room_id: str, limit: int = 50) -> list[ChatMessage]:
        history = self._room_history.get(room_id, [])
        return history[-limit:]


chat_manager = ChatManager()
