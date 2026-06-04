import asyncio
import json
import logging
import random
import string
from fastapi import WebSocket

from . import game

logger = logging.getLogger(__name__)


class LudoPlayerConnection:
    def __init__(self, ws: WebSocket, name: str, user_id: int = None):
        self.ws = ws
        self.name = name
        self.user_id = user_id
        self.color = None
        self.disconnected = False
        self.reconnect_task = None


class LudoRoom:
    def __init__(self, room_id: str, creator: LudoPlayerConnection, password=""):
        self.id = room_id
        self.players = [creator]
        self.password = password
        self.state = game.create_board_state()
        self.color_map = {}  # color_name -> player_idx
        self._broadcast_task = None
        self.timer_task = None
        self.timeout_seconds = 60
        self._move_event = asyncio.Event()
        creator.color = 0
        self.color_map["red"] = 0

    def is_full(self):
        return len(self.players) >= 4

    def player_count(self):
        return len(self.players)

    def add_player(self, conn: LudoPlayerConnection):
        idx = len(self.players)
        conn.color = idx
        colors = game.PLAYER_COLORS
        self.players.append(conn)
        self.color_map[colors[idx]] = idx

    def remove_player(self, player_idx: int):
        if 0 <= player_idx < len(self.players):
            self.players[player_idx] = None
            self._move_event.set()

    def is_player_connected(self, idx):
        return idx < len(self.players) and self.players[idx] is not None and not self.players[idx].disconnected

    def get_connected_count(self):
        return sum(1 for p in self.players if p is not None and not p.disconnected)

    def get_conn_by_color(self, color: str):
        idx = self.color_map.get(color)
        if idx is not None and idx < len(self.players) and self.players[idx]:
            return self.players[idx]
        return None

    def find_player_by_user_id(self, user_id):
        for i, p in enumerate(self.players):
            if p and p.user_id == user_id:
                return i, p
        return None, None

    def reassign_colors(self):
        colors = game.PLAYER_COLORS
        self.color_map = {}
        for i, p in enumerate(self.players):
            if p:
                p.color = i
                self.color_map[colors[i]] = i

    async def broadcast(self, msg, exclude_idx=None):
        msg_str = json.dumps(msg, ensure_ascii=False)
        for i, p in enumerate(self.players):
            if p is not None and not p.disconnected and i != exclude_idx:
                try:
                    await p.ws.send_text(msg_str)
                except Exception:
                    logger.warning(f"Broadcast failed to {p.name}")


class LudoRoomManager:
    def __init__(self):
        self.rooms = {}

    def _generate_id(self):
        for _ in range(100):
            rid = ''.join(random.choices(string.digits, k=4))
            if rid not in self.rooms:
                return rid
        return str(len(self.rooms) + 1)

    async def create_room(self, ws: WebSocket, player_name: str, password="", user_id=None):
        conn = LudoPlayerConnection(ws, player_name, user_id)
        room = LudoRoom(self._generate_id(), conn, password)
        self.rooms[room.id] = room

        await conn.ws.send_json({
            "type": "room_created",
            "room_id": room.id,
            "player_color": "red",
            "player_index": 0,
            "players": [{"name": player_name, "color": "red", "online": True}],
        })
        logger.info(f"Ludo room {room.id} created by {player_name}")
        return room

    async def join_room(self, ws: WebSocket, room_id: str, player_name: str, password="", user_id=None):
        room = self.rooms.get(room_id)
        if not room:
            await ws.send_json({"type": "error", "message": "房间不存在"})
            await ws.close()
            return

        if room.is_full():
            await ws.send_json({"type": "error", "message": "房间已满"})
            await ws.close()
            return

        conn = LudoPlayerConnection(ws, player_name, user_id)
        colors = game.PLAYER_COLORS
        idx = room.player_count()
        conn.color = idx
        room.add_player(conn)

        await conn.ws.send_json({
            "type": "room_joined",
            "room_id": room.id,
            "player_color": colors[idx],
            "player_index": idx,
            "players": [
                {"name": p.name, "color": colors[i], "online": not p.disconnected}
                for i, p in enumerate(room.players) if p
            ],
        })

        await room.broadcast({
            "type": "player_joined",
            "player_name": player_name,
            "player_color": colors[idx],
            "players": [
                {"name": p.name, "color": colors[i], "online": not p.disconnected}
                for i, p in enumerate(room.players) if p
            ],
        }, exclude_idx=idx)

        if room.is_full():
            await self._start_game(room)

        logger.info(f"{player_name} joined ludo room {room_id}")

    async def handle_message(self, room: LudoRoom, player_idx: int, msg: dict):
        msg_type = msg.get("type")

        if msg_type == "roll_dice":
            await self._handle_roll(room, player_idx)
        elif msg_type == "move_piece":
            piece_idx = msg.get("piece_index")
            if piece_idx is not None:
                await self._handle_move(room, player_idx, piece_idx)
        elif msg_type == "leave_room":
            await self._handle_leave(room, player_idx)
        elif msg_type == "chat":
            player = room.players[player_idx]
            await room.broadcast({
                "type": "chat",
                "from": player.name,
                "message": msg.get("message", ""),
            })

    async def _handle_roll(self, room: LudoRoom, player_idx: int):
        state = room.state
        valid, err = game.is_valid_roll(state, player_idx)
        if not valid:
            await self._send_error(room.players[player_idx], err)
            return

        value = game.roll_dice()
        state["dice_value"] = value
        state["rolled_this_turn"] = True

        player = room.players[player_idx]
        await room.broadcast({
            "type": "dice_rolled",
            "player": game.PLAYER_COLORS[player_idx],
            "value": value,
        })

        playable = game.get_playable_pieces(state, player_idx, value)
        if not playable:
            await self._advance_turn(room, player_idx)
        else:
            await player.ws.send_json({
                "type": "your_move",
                "playable_pieces": playable,
                "dice_value": value,
            })

        if value == 6:
            state["consecutive_sixes"] += 1
        else:
            state["consecutive_sixes"] = 0

    async def _handle_move(self, room: LudoRoom, player_idx: int, piece_idx: int):
        state = room.state
        if state["game_over"]:
            return
        if state["current_turn"] != player_idx:
            await self._send_error(room.players[player_idx], "还没轮到你")
            return
        if not state["rolled_this_turn"]:
            await self._send_error(room.players[player_idx], "请先掷骰子")
            return

        playable = game.get_playable_pieces(state, player_idx, state["dice_value"])
        if piece_idx not in playable:
            await self._send_error(room.players[player_idx], "该棋子无法移动")
            return

        result = game.execute_move(state, player_idx, piece_idx)
        player_color = game.PLAYER_COLORS[player_idx]

        await room.broadcast({
            "type": "piece_moved",
            "player": player_color,
            "piece_index": piece_idx,
            "new_pos": result.get("new_pos"),
            "entered": result.get("entered", False),
            "finished": result.get("finished", False),
            "state": state["pieces"][player_idx][piece_idx]["state"],
        })

        if result.get("captured"):
            cap = result["captured"]
            cap_color = game.PLAYER_COLORS[cap["player"]]
            await room.broadcast({
                "type": "piece_captured",
                "by_player": player_color,
                "by_piece": piece_idx,
                "target_player": cap_color,
                "target_piece": cap["piece"],
            })

        if state["game_over"]:
            await room.broadcast({
                "type": "game_over",
                "winner": player_color,
                "reason": "全部到达终点",
            })
            return

        dice = state["dice_value"]
        if dice == 6 and state["consecutive_sixes"] < 3:
            state["rolled_this_turn"] = False
            state["dice_value"] = None
            await room.broadcast({
                "type": "extra_turn",
                "player": player_color,
            })
            await self._start_timer(room, player_idx)
        else:
            if dice == 6 and state["consecutive_sixes"] >= 3:
                for p in state["pieces"][player_idx]:
                    if p["state"] == "active":
                        p["state"] = "home"
                        p["steps"] = 0
                        p["pos"] = -1
                await room.broadcast({
                    "type": "three_sixes_penalty",
                    "player": player_color,
                })
            await self._advance_turn(room, player_idx)

    async def _advance_turn(self, room: LudoRoom, current_idx: int):
        state = room.state
        state["rolled_this_turn"] = False
        state["dice_value"] = None
        state["consecutive_sixes"] = 0

        if state["game_over"]:
            return

        next_idx = (current_idx + 1) % 4
        while room.players[next_idx] is None:
            next_idx = (next_idx + 1) % 4

        state["current_turn"] = next_idx
        next_color = game.PLAYER_COLORS[next_idx]
        await room.broadcast({
            "type": "your_turn",
            "player": next_color,
            "player_index": next_idx,
        })
        await self._start_timer(room, next_idx)

    async def _start_timer(self, room: LudoRoom, player_idx: int):
        if room.timer_task:
            room.timer_task.cancel()
        room.timer_task = asyncio.create_task(self._timer_loop(room, player_idx))

    async def _timer_loop(self, room: LudoRoom, player_idx: int):
        try:
            for remaining in range(room.timeout_seconds, 0, -1):
                if room.state["game_over"]:
                    return
                if room.state["current_turn"] != player_idx:
                    return
                if remaining % 10 == 0 or remaining <= 5:
                    p = room.players[player_idx]
                    if p and not p.disconnected:
                        try:
                            await p.ws.send_json({
                                "type": "timer",
                                "remaining": remaining,
                            })
                        except Exception:
                            pass
                await asyncio.sleep(1)
            # Timeout
            if room.state["current_turn"] == player_idx and not room.state["game_over"]:
                player_color = game.PLAYER_COLORS[player_idx]
                await room.broadcast({
                    "type": "game_over",
                    "winner": game.PLAYER_COLORS[(player_idx + 1) % 4],
                    "reason": f"{player_color}超时",
                })
                room.state["game_over"] = True
        except asyncio.CancelledError:
            pass

    async def _handle_leave(self, room: LudoRoom, player_idx: int):
        player = room.players[player_idx]
        if not player:
            return
        player_color = game.PLAYER_COLORS[player_idx]
        room.players[player_idx] = None
        await room.broadcast({
            "type": "player_left",
            "player_name": player.name,
            "player_color": player_color,
        })
        if sum(1 for p in room.players if p is not None) == 0:
            self.remove_room(room.id)

    async def _start_game(self, room: LudoRoom):
        colors = game.PLAYER_COLORS
        await room.broadcast({
            "type": "game_start",
            "players": [
                {"name": p.name, "color": colors[i], "online": not p.disconnected}
                for i, p in enumerate(room.players) if p
            ],
        })
        first_color = colors[0]
        await room.broadcast({
            "type": "your_turn",
            "player": first_color,
            "player_index": 0,
        })
        await self._start_timer(room, 0)

    async def _send_error(self, conn: LudoPlayerConnection, message: str):
        if conn and not conn.disconnected:
            try:
                await conn.ws.send_json({"type": "error", "message": message})
            except Exception:
                pass

    async def handle_disconnect(self, room: LudoRoom, player_idx: int):
        player = room.players[player_idx]
        if player:
            player.disconnected = True
            player_color = game.PLAYER_COLORS[player_idx]
            await room.broadcast({
                "type": "player_disconnected",
                "player_name": player.name,
                "player_color": player_color,
            })
            if room.timer_task:
                room.timer_task.cancel()

            async def reconnect_timeout():
                await asyncio.sleep(30)
                if player.disconnected:
                    await room.broadcast({
                        "type": "player_left",
                        "player_name": player.name,
                        "player_color": player_color,
                    })
                    room.players[player_idx] = None
                    if room.state["current_turn"] == player_idx:
                        await self._advance_turn(room, player_idx)
                    if sum(1 for p in room.players if p is not None) == 0:
                        self.remove_room(room.id)

            player.reconnect_task = asyncio.create_task(reconnect_timeout())

    async def handle_reconnect(self, room: LudoRoom, player_idx: int, ws: WebSocket):
        player = room.players[player_idx]
        if player and player.reconnect_task:
            player.reconnect_task.cancel()
            player.reconnect_task = None
        player.ws = ws
        player.disconnected = False
        colors = game.PLAYER_COLORS
        player_color = colors[player_idx]
        await ws.send_json({
            "type": "reconnected",
            "player_color": player_color,
            "player_index": player_idx,
            "state": self._build_state_for(room, player_idx),
        })
        await room.broadcast({
            "type": "player_reconnected",
            "player_name": player.name,
            "player_color": player_color,
        })

    def _build_state_for(self, room: LudoRoom, player_idx: int):
        return {
            "board_state": room.state,
            "players": [
                {"name": p.name, "color": game.PLAYER_COLORS[i], "online": not p.disconnected}
                for i, p in enumerate(room.players) if p
            ],
        }

    def get_room(self, room_id):
        return self.rooms.get(room_id)

    def remove_room(self, room_id):
        self.rooms.pop(room_id, None)
        logger.info(f"Ludo room {room_id} removed")

    def list_open_rooms(self):
        return [
            {
                "room_id": room.id,
                "host_name": room.players[0].name if room.players[0] else "",
                "player_count": room.player_count(),
                "max_players": 4,
                "has_password": bool(room.password),
            }
            for room in self.rooms.values()
            if not room.is_full() and not room.state["game_over"]
        ]

    def find_room_by_user_id(self, user_id):
        for rid, room in self.rooms.items():
            for i, p in enumerate(room.players):
                if p and p.user_id == user_id:
                    return room, i
        return None, None


manager = LudoRoomManager()
