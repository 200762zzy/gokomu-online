import json, asyncio, logging, random
from fastapi import WebSocket
from . import game
from ..ws.handler import register_global_connection, unregister_global_connection, notify_friends_online, notify_friends_offline

logger = logging.getLogger(__name__)

_cc_ws_counter = 0


class CCPlayerConnection:
    def __init__(self, ws: WebSocket, name: str):
        self.ws = ws
        self.name = name
        self.user_id: int | None = None
        self.disconnected = False
        self.reconnect_task = None


class CCRoom:
    def __init__(self, room_id: str, red: CCPlayerConnection, password: str = ""):
        self.id = room_id
        self.players: dict[str, CCPlayerConnection | None] = {"red": red, "black": None}
        self.board = game.create_board()
        self.current_turn = game.RED
        self.move_history: list[dict] = []
        self.game_over = False
        self.winner: str | None = None
        self.win_reason: str | None = None
        self.draw_offer_by: str | None = None
        self.red_name = red.name
        self.black_name: str | None = None
        self.red_user_id: int | None = None
        self.red_elo: int | None = None
        self.black_user_id: int | None = None
        self.black_elo: int | None = None
        self.spectators: list[CCPlayerConnection] = []
        self.password = password
        self.position_counts: dict = {}  # position_hash -> count
        self.consecutive_checks: dict[str, int] = {"red": 0, "black": 0}
        self.move_history_for_repetition: list = []

    @property
    def is_full(self):
        return self.players["black"] is not None

    @property
    def player_count(self):
        count = 0
        if self.players["red"]: count += 1
        if self.players["black"]: count += 1
        return count

    def get_opponent_color(self, color: str) -> str:
        return "black" if color == "red" else "red"

    def to_dict(self) -> dict:
        from ..services.title_service import get_title
        red_title = get_title(self.red_elo)
        black_title = get_title(self.black_elo) if self.black_elo else None
        return {
            "room_id": self.id,
            "red_name": self.red_name,
            "black_name": self.black_name,
            "spectator_count": len(self.spectators),
            "game_over": self.game_over,
            "move_count": len(self.move_history),
            "has_password": bool(self.password),
            "red_title": red_title.model_dump() if red_title else None,
            "black_title": black_title.model_dump() if black_title else None,
        }


class CCRoomManager:
    def __init__(self):
        self.rooms: dict[str, CCRoom] = {}

    def _generate_id(self) -> str:
        for _ in range(100):
            rid = f"{random.randint(0, 9999):04d}"
            if rid not in self.rooms:
                return rid
        raise RuntimeError("No available room IDs")

    async def create_room(self, ws, player_name, password=""):
        room_id = self._generate_id()
        player = CCPlayerConnection(ws, player_name)
        room = CCRoom(room_id, player, password)
        self.rooms[room_id] = room
        logger.info(f"CC Room {room_id} created by {player_name}")
        return room_id, "red"

    async def join_room(self, room_id, ws, player_name, password=""):
        room = self.rooms.get(room_id)
        if room is None: return None
        if room.is_full: return None
        if room.password and room.password != password: return "password_required"
        room.players["black"] = CCPlayerConnection(ws, player_name)
        room.black_name = player_name
        logger.info(f"{player_name} joined CC room {room_id}")
        return "black"

    def get_room(self, room_id):
        return self.rooms.get(room_id)

    def remove_room(self, room_id):
        self.rooms.pop(room_id, None)
        logger.info(f"CC Room {room_id} removed")

    def list_open_rooms(self):
        return [r.to_dict() for r in self.rooms.values() if not r.is_full and not r.game_over]

    def list_spectatable_rooms(self):
        return [r.to_dict() for r in self.rooms.values() if r.is_full and not r.game_over]

    def find_room_by_user_id(self, user_id: int):
        for room in self.rooms.values():
            if room.red_user_id == user_id:
                return room, "red"
            if room.black_user_id == user_id:
                return room, "black"
            for color, player in room.players.items():
                if player and player.user_id == user_id:
                    return room, color
        return None, None

    def _check_repetition_and_perpetual(self, room: CCRoom, color: str, player: int) -> dict | None:
        ph = game.position_hash(room.board)
        room.position_counts[ph] = room.position_counts.get(ph, 0) + 1
        room.move_history_for_repetition.append(ph)
        if room.position_counts[ph] >= 3:
            room.game_over = True
            room.winner = None
            room.win_reason = "三次重复局面 和棋"
            return {"ok": True, "checkmate": True, "winner": None, "reason": "三次重复局面 和棋"}
        enemy_color = "black" if color == "red" else "red"
        if game.is_in_check(room.board, player == game.RED and game.BLACK or game.RED):
            room.consecutive_checks[color] += 1
        else:
            room.consecutive_checks[color] = 0
        if room.consecutive_checks[color] >= 3:
            room.game_over = True
            room.winner = enemy_color
            room.win_reason = f"{color}长将判负"
            return {"ok": True, "checkmate": True, "winner": enemy_color, "reason": f"{color}长将判负"}
        return None

    def handle_move_piece(self, room: CCRoom, color: str, from_r: int, from_c: int, to_r: int, to_c: int) -> dict:
        if room.game_over:
            return {"ok": False, "error": "游戏已结束"}
        player = game.RED if color == "red" else game.BLACK
        if player != room.current_turn:
            return {"ok": False, "error": "未轮到你走棋"}
        piece = room.board[from_r][from_c]
        if game.get_piece_color(piece) != player:
            return {"ok": False, "error": "这不是你的棋子"}
        valid = game.get_valid_moves(room.board, from_r, from_c)
        if (to_r, to_c) not in valid:
            return {"ok": False, "error": "非法走法"}
        captured = room.board[to_r][to_c]
        game.make_move(room.board, from_r, from_c, to_r, to_c)
        room.move_history.append({
            "from_r": from_r, "from_c": from_c,
            "to_r": to_r, "to_c": to_c,
            "player": player,
            "captured": captured,
        })
        enemy = game.BLACK if player == game.RED else game.RED
        if game.is_checkmate(room.board, enemy):
            room.game_over = True
            room.winner = color
            room.win_reason = "将杀"
            return {"ok": True, "checkmate": True, "winner": color, "reason": "将杀"}
        if game.is_stalemate(room.board, enemy):
            room.game_over = True
            room.winner = color
            room.win_reason = "困毙"
            return {"ok": True, "checkmate": True, "winner": color, "reason": "困毙"}
        room.current_turn = enemy
        rep_result = self._check_repetition_and_perpetual(room, color, player)
        if rep_result:
            return rep_result
        in_check = game.is_in_check(room.board, enemy)
        return {"ok": True, "checkmate": False, "in_check": in_check,
                "check_color": "red" if enemy == game.RED else "black" if in_check else None}

    def handle_resign(self, room: CCRoom, color: str) -> dict:
        if room.game_over:
            return {"ok": False, "error": "游戏已结束"}
        room.game_over = True
        winner_color = room.get_opponent_color(color)
        room.winner = winner_color
        room.win_reason = f"{color}认负"
        return {"ok": True, "winner": winner_color, "reason": f"{color}认负"}

    def handle_draw_request(self, room: CCRoom, color: str) -> dict:
        if room.game_over:
            return {"ok": False, "error": "游戏已结束"}
        if room.draw_offer_by:
            return {"ok": False, "error": "已有和棋提议"}
        room.draw_offer_by = color
        return {"ok": True}

    def handle_draw_response(self, room: CCRoom, color: str, accept: bool) -> dict:
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


cc_room_manager = CCRoomManager()


async def send_msg(ws: WebSocket, msg: dict):
    try:
        await ws.send_json(msg)
    except Exception:
        pass


async def broadcast(room: CCRoom, msg: dict, exclude_ws=None):
    for player in room.players.values():
        if player and player.ws != exclude_ws:
            await send_msg(player.ws, msg)
    for spec in getattr(room, "spectators", []):
        if spec.ws != exclude_ws:
            await send_msg(spec.ws, msg)


async def handle_cc_websocket(ws: WebSocket):
    await ws.accept()
    global _cc_ws_counter
    _cc_ws_counter += 1
    ws_id = _cc_ws_counter

    logger.info(f"New CC WebSocket connection (id={ws_id})")

    user_id = None
    username = None
    current_room: CCRoom | None = None
    current_color: str | None = None
    is_spectator = False

    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=10.0)
        data = json.loads(raw)
        if data.get("type") == "auth":
            from ..services.auth_service import verify_token
            token = data.get("token", "")
            uid = verify_token(token, "access")
            if uid:
                from ..database import async_session_factory
                from ..models.user import User
                async with async_session_factory() as db:
                    user = await db.get(User, uid)
                if user:
                    user_id = user.id
                    username = user.username
        if not user_id:
            await send_msg(ws, {"type": "error", "message": "认证失败"})
            await ws.close()
            return
        await register_global_connection(user_id, ws_id, ws)
        await notify_friends_online(user_id, username)
        await send_msg(ws, {"type": "auth_ok", "user_id": user_id, "username": username})
    except (asyncio.TimeoutError, json.JSONDecodeError, WebSocketDisconnect):
        from fastapi import WebSocketDisconnect
        await ws.close()
        return

    try:
        from fastapi import WebSocketDisconnect
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_msg(ws, {"type": "error", "message": "无效的JSON"})
                continue

            msg_type = data.get("type", "")

            if msg_type == "create_room":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                name = data.get("player_name", username)
                password = data.get("password", "")
                room_id, color = await cc_room_manager.create_room(ws, name, password)
                current_room = cc_room_manager.get_room(room_id)
                current_color = color
                current_room.red_user_id = user_id
                if current_room.players["red"]:
                    current_room.players["red"].user_id = user_id
                from ..database import async_session_factory
                from ..models.user import User
                async with async_session_factory() as db:
                    u = await db.get(User, user_id)
                    if u: current_room.red_elo = u.elo
                await send_msg(ws, {
                    "type": "room_created",
                    "room_id": room_id,
                    "player_color": color,
                    "has_password": bool(password),
                })

            elif msg_type == "join_room":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                room_id = data.get("room_id", "")
                name = data.get("player_name", username)
                password = data.get("password", "")
                color = await cc_room_manager.join_room(room_id, ws, name, password)
                if color is None:
                    await send_msg(ws, {"type": "error", "message": "房间不存在或已满"})
                    continue
                if color == "password_required":
                    await send_msg(ws, {"type": "error", "message": "房间需要密码"})
                    continue
                current_room = cc_room_manager.get_room(room_id)
                current_color = color
                if current_room.players["black"]:
                    current_room.players["black"].user_id = user_id
                if current_color == "black":
                    current_room.black_user_id = user_id

                from ..database import async_session_factory
                from ..models.user import User
                from ..services.title_service import get_title
                async with async_session_factory() as db:
                    u = await db.get(User, user_id)
                    if u: current_room.black_elo = u.elo

                opponent = current_room.players[current_room.get_opponent_color(color)]
                opp_name = opponent.name if opponent else "未知"
                opp_title = get_title(current_room.red_elo)
                player_title = get_title(current_room.black_elo)

                await send_msg(ws, {
                    "type": "room_joined",
                    "room_id": room_id,
                    "player_color": color,
                    "opponent_name": opp_name,
                    "opponent_title": opp_title.model_dump() if opp_title else None,
                    "board": game.board_to_api(current_room.board),
                    "current_turn": "red" if current_room.current_turn == game.RED else "black",
                    "your_turn": current_room.current_turn == (game.RED if color == "red" else game.BLACK),
                    "move_history": current_room.move_history,
                })

                for c_name, player in current_room.players.items():
                    if player:
                        your_turn = current_room.current_turn == (game.RED if c_name == "red" else game.BLACK)
                        await send_msg(player.ws, {
                            "type": "game_state",
                            "board": game.board_to_api(current_room.board),
                            "current_turn": "red" if current_room.current_turn == game.RED else "black",
                            "your_turn": your_turn,
                            "move_history": current_room.move_history,
                        })

                await broadcast(current_room, {
                    "type": "opponent_joined",
                    "player_name": name,
                    "player_title": player_title.model_dump() if player_title else None,
                }, exclude_ws=ws)

            elif msg_type == "move_piece":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                from_r = data.get("from_row")
                from_c = data.get("from_col")
                to_r = data.get("to_row")
                to_c = data.get("to_col")
                if any(v is None for v in [from_r, from_c, to_r, to_c]):
                    await send_msg(ws, {"type": "error", "message": "缺少走法坐标"})
                    continue
                result = cc_room_manager.handle_move_piece(current_room, current_color, from_r, from_c, to_r, to_c)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue

                captured = current_room.move_history[-1]["captured"] if current_room.move_history else 0
                await broadcast(current_room, {
                    "type": "piece_moved",
                    "from_row": from_r,
                    "from_col": from_c,
                    "to_row": to_r,
                    "to_col": to_c,
                    "player": current_color,
                    "captured": captured,
                    "current_turn": "red" if current_room.current_turn == game.RED else "black",
                    "in_check": result.get("check_color"),
                })

                if result.get("checkmate"):
                    asyncio.create_task(_async_save_cc_game(current_room))
                    await broadcast(current_room, {
                        "type": "game_over",
                        "winner": result["winner"],
                        "reason": result["reason"],
                    })

                for c_name, player in current_room.players.items():
                    if player:
                        await send_msg(player.ws, {
                            "type": "your_turn",
                            "your_turn": current_room.current_turn == (game.RED if c_name == "red" else game.BLACK),
                        })

            elif msg_type == "resign":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = cc_room_manager.handle_resign(current_room, current_color)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                asyncio.create_task(_async_save_cc_game(current_room))
                await broadcast(current_room, {
                    "type": "game_over",
                    "winner": result["winner"],
                    "reason": result["reason"],
                })

            elif msg_type == "draw_request":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = cc_room_manager.handle_draw_request(current_room, current_color)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                opponent_color = current_room.get_opponent_color(current_color)
                opponent = current_room.players[opponent_color]
                if opponent:
                    await send_msg(opponent.ws, {"type": "draw_offered", "by": current_color})

            elif msg_type == "draw_response":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                accept = data.get("accept", False)
                result = cc_room_manager.handle_draw_response(current_room, current_color, accept)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                if result.get("accept"):
                    asyncio.create_task(_async_save_cc_game(current_room))
                    await broadcast(current_room, {
                        "type": "game_over",
                        "winner": None,
                        "reason": "和棋",
                    })
                else:
                    await broadcast(current_room, {
                        "type": "draw_declined",
                        "by": current_color,
                    })

            elif msg_type == "leave_room":
                if current_room:
                    opponent_color = current_room.get_opponent_color(current_color)
                    opponent = current_room.players[opponent_color]
                    if opponent:
                        await send_msg(opponent.ws, {
                            "type": "opponent_left",
                            "message": "对手离开了房间",
                        })
                    if is_spectator:
                        current_room.spectators = [s for s in current_room.spectators if s.ws != ws]
                    elif current_room.player_count <= 1:
                        cc_room_manager.remove_room(current_room.id)
                    else:
                        current_room.players[current_color] = None
                    current_room = None
                    current_color = None
                    is_spectator = False

            elif msg_type == "spectate_room":
                room_id = data.get("room_id", "")
                target = cc_room_manager.get_room(room_id)
                if not target:
                    await send_msg(ws, {"type": "error", "message": "房间不存在"})
                    continue
                spec = CCPlayerConnection(ws, username)
                spec.user_id = user_id
                target.spectators.append(spec)
                current_room = target
                is_spectator = True
                await send_msg(ws, {
                    "type": "spectate_joined",
                    "room_id": room_id,
                    "board": game.board_to_api(target.board),
                    "current_turn": "red" if target.current_turn == game.RED else "black",
                    "move_history": target.move_history,
                    "red_name": target.red_name,
                    "black_name": target.black_name,
                })

            elif msg_type == "sync":
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "不在房间中"})
                    continue
                opponent_color = current_room.get_opponent_color(current_color) if current_color else None
                opponent = current_room.players[opponent_color] if opponent_color else None
                opp_name = opponent.name if opponent else (current_room.black_name if current_color == "red" else current_room.red_name)
                your_turn = current_room.current_turn == (game.RED if current_color == "red" else game.BLACK)
                in_check = game.is_in_check(current_room.board, current_room.current_turn)
                from ..services.title_service import get_title
                opp_elo = current_room.black_elo if current_color == "red" else current_room.red_elo
                opp_title = get_title(opp_elo)
                await send_msg(ws, {
                    "type": "sync_room",
                    "player_color": current_color,
                    "opponent_name": opp_name or "等待对手加入...",
                    "opponent_title": opp_title.model_dump() if opp_title else None,
                    "board": game.board_to_api(current_room.board),
                    "current_turn": "red" if current_room.current_turn == game.RED else "black",
                    "your_turn": your_turn,
                    "move_history": current_room.move_history,
                    "game_over": current_room.game_over,
                    "winner": current_room.winner,
                    "in_check": "red" if in_check and current_room.current_turn == game.RED else "black" if in_check else None,
                })

            elif msg_type == "chat":
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "不在房间中"})
                    continue
                message = data.get("message", "").strip()
                if not message or len(message) > 500:
                    continue
                await broadcast(current_room, {
                    "type": "chat",
                    "from": username,
                    "from_user_id": user_id,
                    "message": message,
                })

    except WebSocketDisconnect:
        logger.info(f"CC WebSocket disconnected: {username}")
    except Exception as e:
        logger.error(f"CC WebSocket error: {e}")
    finally:
        if user_id:
            await notify_friends_offline(user_id)
            await unregister_global_connection(user_id, ws_id)
        if current_room and not is_spectator:
            color = current_color
            opponent_color = current_room.get_opponent_color(color) if color else None
            opponent = current_room.players[opponent_color] if opponent_color else None
            if opponent:
                await send_msg(opponent.ws, {
                    "type": "opponent_disconnected",
                    "message": "对手断线了",
                })
            current_room.players[color] = None
            if current_room.player_count <= 1:
                cc_room_manager.remove_room(current_room.id)


async def _async_save_cc_game(room: CCRoom):
    try:
        red_id = getattr(room, "red_user_id", None)
        black_id = getattr(room, "black_user_id", None)
        if not red_id or not black_id:
            return
        from ..services.game_service import save_game
        from ..database import async_session_factory
        async with async_session_factory() as db:
            moves = [
                {"from_r": m["from_r"], "from_c": m["from_c"],
                 "to_r": m["to_r"], "to_c": m["to_c"],
                 "player": "red" if m["player"] == game.RED else "black"}
                for m in room.move_history
            ]
            mapped_winner = {"red": "white", "black": "black"}.get(room.winner) if room.winner else None
            await save_game(
                db=db,
                black_id=black_id,
                white_id=red_id,
                winner=mapped_winner,
                reason=room.win_reason,
                moves=moves,
                game_type="chinese_chess",
            )
    except Exception as e:
        logger.error(f"Failed to save CC game: {e}")
