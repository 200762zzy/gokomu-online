import random
import asyncio
import logging
from fastapi import WebSocket
from . import game
from .services.title_service import get_title

logger = logging.getLogger(__name__)


class PlayerConnection:
    def __init__(self, ws: WebSocket, name: str):
        self.ws = ws
        self.name = name
        self.user_id: int | None = None
        self.disconnected: bool = False
        self.reconnect_task: asyncio.Task | None = None


class Room:
    def __init__(self, room_id: str, black: PlayerConnection, password: str = "",
                 initial_time_ms: int = 1800000, increment_ms: int = 30000):
        self.id = room_id
        self.players: dict[str, PlayerConnection | None] = {"black": black, "white": None}
        self.board = game.create_board()
        self.current_turn = game.BLACK
        self.move_history: list[dict] = []
        self.game_over = False
        self.winner: str | None = None
        self.win_reason: str | None = None
        self.draw_offer_by: str | None = None
        self.undo_request_by: str | None = None
        self.black_name = black.name
        self.white_name: str | None = None
        self.black_user_id: int | None = None
        self.white_user_id: int | None = None
        self.black_elo: int = 1000
        self.white_elo: int | None = None
        self.spectators: list[PlayerConnection] = []
        self.password = password
        self.black_time_remaining: int = initial_time_ms
        self.white_time_remaining: int = initial_time_ms
        self.increment: int = increment_ms
        self.timer_task: asyncio.Task | None = None
        self.timer_active: bool = False

    @property
    def is_full(self) -> bool:
        return self.players["white"] is not None

    @property
    def player_count(self) -> int:
        count = 0
        if self.players["black"]:
            count += 1
        if self.players["white"]:
            count += 1
        return count

    def get_opponent_color(self, color: str) -> str:
        return "white" if color == "black" else "black"

    def to_dict(self) -> dict:
        return {
            "room_id": self.id,
            "black_name": self.black_name,
            "white_name": self.white_name,
            "spectator_count": len(self.spectators),
            "game_over": self.game_over,
            "move_count": len(self.move_history),
            "has_password": bool(self.password),
            "increment_ms": self.increment,
            "black_title": get_title(self.black_elo).model_dump(),
            "white_title": get_title(self.white_elo or 1000).model_dump(),
        }


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Room] = {}

    def _generate_id(self) -> str:
        for _ in range(100):
            rid = f"{random.randint(0, 9999):04d}"
            if rid not in self.rooms:
                return rid
        raise RuntimeError("No available room IDs")

    async def create_room(self, ws: WebSocket, player_name: str,
                          password: str = "",
                          initial_time_ms: int = 1800000,
                          increment_ms: int = 30000) -> tuple[str, str]:
        room_id = self._generate_id()
        player = PlayerConnection(ws, player_name)
        room = Room(room_id, player, password, initial_time_ms, increment_ms)
        self.rooms[room_id] = room
        logger.info(f"Room {room_id} created by {player_name} {'(password)' if password else ''}")
        return room_id, "black"

    async def join_room(self, room_id: str, ws: WebSocket, player_name: str,
                        password: str = "") -> str | None:
        room = self.rooms.get(room_id)
        if room is None:
            return None
        if room.is_full:
            return None
        if room.password and room.password != password:
            return "password_required"
        room.players["white"] = PlayerConnection(ws, player_name)
        room.white_name = player_name
        logger.info(f"{player_name} joined room {room_id}")
        return "white"

    def get_room(self, room_id: str) -> Room | None:
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str):
        self.rooms.pop(room_id, None)
        logger.info(f"Room {room_id} removed")

    def list_open_rooms(self) -> list[dict]:
        result = []
        for room in self.rooms.values():
            if not room.is_full and not room.game_over:
                result.append(room.to_dict())
        return result

    def list_spectatable_rooms(self) -> list[dict]:
        result = []
        for room in self.rooms.values():
            if room.is_full and not room.game_over:
                d = room.to_dict()
                d["black_user_id"] = room.black_user_id
                d["white_user_id"] = room.white_user_id
                result.append(d)
        return result

    async def handle_place_stone(self, room: Room, color: str, row: int, col: int) -> dict:
        if room.game_over:
            return {"ok": False, "error": "游戏已结束"}

        player = game.BLACK if color == "black" else game.WHITE
        if player != room.current_turn:
            return {"ok": False, "error": "未轮到你落子"}

        if not game.is_valid_move(room.board, row, col):
            return {"ok": False, "error": "无效落子位置"}

        if player == game.BLACK:
            reason = game.is_forbidden(room.board, row, col, game.BLACK)
            if reason:
                return {"ok": False, "error": f"禁手：{reason}"}

        game.place_stone(room.board, row, col, player)
        room.move_history.append({"row": row, "col": col, "player": player})

        win = game.check_win(room.board, row, col)
        if win is not None:
            room.game_over = True
            room.winner = color
            room.win_reason = "五子连珠"
            return {"ok": True, "win": True, "winner": color, "reason": "五子连珠"}

        room.current_turn = game.WHITE if player == game.BLACK else game.BLACK
        return {"ok": True, "win": False}

    async def handle_resign(self, room: Room, color: str) -> dict:
        if room.game_over:
            return {"ok": False, "error": "游戏已结束"}
        room.game_over = True
        winner_color = room.get_opponent_color(color)
        room.winner = winner_color
        room.win_reason = f"{color}认负"
        return {"ok": True, "winner": winner_color, "reason": f"{color}认负"}

    async def handle_undo_request(self, room: Room, color: str) -> dict:
        if room.game_over:
            return {"ok": False, "error": "游戏已结束"}
        player = game.BLACK if color == "black" else game.WHITE
        if player != room.current_turn:
            return {"ok": False, "error": "只能在轮到你时请求悔棋"}
        if room.undo_request_by:
            return {"ok": False, "error": "已有悔棋请求"}
        if len(room.move_history) == 0:
            return {"ok": False, "error": "没有可悔的棋"}
        room.undo_request_by = color
        return {"ok": True}

    async def handle_undo_response(self, room: Room, color: str, accept: bool) -> dict:
        if not room.undo_request_by:
            return {"ok": False, "error": "没有悔棋请求"}
        if room.undo_request_by == color:
            return {"ok": False, "error": "不能回应自己的请求"}
        if not accept:
            room.undo_request_by = None
            return {"ok": True, "accept": False}

        last = room.move_history.pop()
        room.board[last["row"]][last["col"]] = game.EMPTY
        if len(room.move_history) > 0:
            last2 = room.move_history[-1]
            last2_color = "black" if last2["player"] == game.BLACK else "white"
            if last2_color == room.undo_request_by:
                room.board[last2["row"]][last2["col"]] = game.EMPTY
                room.move_history.pop()

        undo_player = game.BLACK if room.undo_request_by == "black" else game.WHITE
        room.current_turn = undo_player
        room.undo_request_by = None
        return {"ok": True, "accept": True}

    async def handle_draw_request(self, room: Room, color: str) -> dict:
        if room.game_over:
            return {"ok": False, "error": "游戏已结束"}
        if room.draw_offer_by:
            return {"ok": False, "error": "已有和棋提议"}
        room.draw_offer_by = color
        return {"ok": True}

    async def handle_draw_response(self, room: Room, color: str, accept: bool) -> dict:
        if not room.draw_offer_by:
            return {"ok": False, "error": "没有和棋提议"}
        if room.draw_offer_by == color:
            return {"ok": False, "error": "不能回应自己的提议"}

        if accept:
            room.game_over = True
            room.winner = None
            room.win_reason = "和棋"
            room.draw_offer_by = None
            return {"ok": True, "accept": True, "reason": "和棋"}
        else:
            room.draw_offer_by = None
            return {"ok": True, "accept": False}


    def find_room_by_user_id(self, user_id: int) -> tuple[Room | None, str | None]:
        for room in self.rooms.values():
            for color, player in room.players.items():
                if player and player.user_id == user_id:
                    return room, color
        return None, None

    def reconnect_player(self, room: Room, color: str, ws: WebSocket) -> bool:
        player = room.players.get(color)
        if not player or not player.disconnected:
            return False
        player.ws = ws
        player.disconnected = False
        if player.reconnect_task:
            player.reconnect_task.cancel()
            player.reconnect_task = None
        return True

    def kick_user_from_rooms(self, user_id: int, reason: str):
        for room in list(self.rooms.values()):
            for color, player in list(room.players.items()):
                if player and player.user_id == user_id:
                    if player.ws:
                        asyncio.ensure_future(player.ws.send_json({
                            "type": "kicked",
                            "reason": reason,
                        }))
                        asyncio.ensure_future(player.ws.close())
                    room.players[color] = None
            room.spectators[:] = [s for s in room.spectators if s.user_id != user_id]

    def list_all_rooms(self) -> list:
        return list(self.rooms.values())

    def close_room(self, room_id: str, reason: str):
        room = self.rooms.pop(room_id, None)
        if not room:
            return
        for player in room.players.values():
            if player and player.ws:
                asyncio.ensure_future(player.ws.send_json({
                    "type": "room_closed",
                    "reason": reason,
                }))
                asyncio.ensure_future(player.ws.close())
        for spec in room.spectators:
            if spec.ws:
                asyncio.ensure_future(spec.ws.send_json({
                    "type": "room_closed",
                    "reason": reason,
                }))
                asyncio.ensure_future(spec.ws.close())

room_manager = RoomManager()
