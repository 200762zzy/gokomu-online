import json
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect

from ..database import async_session_factory
from ..models.user import User
from ..services.auth_service import verify_token
from ..room_manager import room_manager, Room, PlayerConnection
from ..ai_analysis import request_analysis
from ..services.title_service import get_title
from .matchmaker import matchmaker, MatchEntry
from .chat import chat_manager, ChatMessage
from .. import game

logger = logging.getLogger(__name__)

_ws_counter = 0
# Global user -> ws mapping for global chat / private chat / friend online
_global_connections: dict[int, WebSocket] = {}
_global_ws_to_user: dict[int, int] = {}  # ws_id -> user_id
_global_lock = asyncio.Lock()


async def _set_global(user_id: int, ws_id: int, ws: WebSocket):
    async with _global_lock:
        _global_connections[user_id] = ws
        _global_ws_to_user[ws_id] = user_id


async def _remove_global(user_id: int, ws_id: int):
    async with _global_lock:
        _global_connections.pop(user_id, None)
        _global_ws_to_user.pop(ws_id, None)


async def _get_global_ws(user_id: int) -> WebSocket | None:
    async with _global_lock:
        return _global_connections.get(user_id)


async def _notify_friends_online(user_id: int, username: str):
    async with _global_lock:
        for uid, uws in list(_global_connections.items()):
            if uid != user_id and uws:
                asyncio.create_task(send_msg(uws, {"type": "friend_online", "user_id": user_id, "username": username}))


async def _notify_friends_offline(user_id: int):
    async with _global_lock:
        for uid, uws in list(_global_connections.items()):
            if uid != user_id and uws:
                asyncio.create_task(send_msg(uws, {"type": "friend_offline", "user_id": user_id}))


async def _broadcast_global_chat(from_user: str, from_user_id: int, message: str):
    async with _global_lock:
        for uid, uws in list(_global_connections.items()):
            asyncio.create_task(send_msg(uws, {
                "type": "global_chat",
                "from": from_user,
                "from_user_id": from_user_id,
                "message": message,
            }))


async def _send_private_chat(from_user: str, from_user_id: int, to_username: str, message: str):
    async with _global_lock:
        for uid, uws in list(_global_connections.items()):
            asyncio.create_task(send_msg(uws, {
                "type": "private_chat",
                "from": from_user,
                "from_user_id": from_user_id,
                "message": message,
            }))


async def send_msg(ws: WebSocket, msg: dict):
    try:
        await ws.send_json(msg)
    except Exception:
        pass


async def broadcast(room: Room, msg: dict, exclude_ws: WebSocket | None = None):
    for player in room.players.values():
        if player and player.ws != exclude_ws:
            await send_msg(player.ws, msg)
    for spectator in getattr(room, "spectators", []):
        if spectator.ws != exclude_ws:
            await send_msg(spectator.ws, msg)


async def start_timer(room: Room):
    """Background task: tick every second, send updates, handle timeout."""
    room.timer_active = True
    try:
        while room.timer_active and not room.game_over:
            await asyncio.sleep(1)
            if room.game_over or not room.timer_active:
                break
            player = room.current_turn
            if player == game.BLACK:
                room.black_time_remaining -= 1000
            else:
                room.white_time_remaining -= 1000

            await broadcast(room, {
                "type": "timer_update",
                "black_time": room.black_time_remaining,
                "white_time": room.white_time_remaining,
            })

            if room.black_time_remaining <= 0:
                room.game_over = True
                room.winner = "white"
                room.win_reason = "黑方超时"
                await broadcast(room, {"type": "game_over", "winner": "white", "reason": "黑方超时"})
                break
            if room.white_time_remaining <= 0:
                room.game_over = True
                room.winner = "black"
                room.win_reason = "白方超时"
                await broadcast(room, {"type": "game_over", "winner": "black", "reason": "白方超时"})
                break
    except asyncio.CancelledError:
        pass
    finally:
        room.timer_active = False


def reset_timer(room: Room):
    """Add increment to the player who just moved."""
    if room.current_turn == game.WHITE:  # black just moved
        room.black_time_remaining += room.increment
    else:  # white just moved
        room.white_time_remaining += room.increment


RECONNECT_TIMEOUT = 30


async def handle_websocket(ws: WebSocket):
    global _ws_counter
    _ws_counter += 1
    ws_id = _ws_counter

    await ws.accept()
    logger.info(f"New WebSocket connection (id={ws_id})")

    user: User | None = None
    current_room: Room | None = None
    current_color: str | None = None
    is_spectator = False

    # Wait for auth
    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=10.0)
        data = json.loads(raw)
        if data.get("type") == "auth":
            token = data.get("token", "")
            user_id = verify_token(token, "access")
            if user_id:
                async with async_session_factory() as db:
                    user = await db.get(User, user_id)
        if not user:
            await send_msg(ws, {"type": "error", "message": "认证失败，请重新登录"})
            await ws.close()
            return

        # Check if user has a disconnected room to reconnect to
        pending_room, pending_color = room_manager.find_room_by_user_id(user.id)
        if pending_room and pending_color:
            player = pending_room.players.get(pending_color)
            if player and player.disconnected:
                room_manager.reconnect_player(pending_room, pending_color, ws)
                current_room = pending_room
                current_color = pending_color
                await _set_global(user.id, ws_id, ws)
                await send_msg(ws, {
                    "type": "reconnected",
                    "room_id": pending_room.id,
                    "player_color": pending_color,
                    "board": _board_for_api(pending_room.board),
                    "current_turn": _color_name(pending_room.current_turn),
                    "move_history": pending_room.move_history,
                    "black_name": pending_room.black_name,
                    "white_name": pending_room.white_name,
                    "black_time": pending_room.black_time_remaining,
                    "white_time": pending_room.white_time_remaining,
                    "your_title": get_title(user.elo).model_dump(),
                    "opponent_title": get_title(pending_room.black_elo if pending_color == "white" else (pending_room.white_elo or 1000)).model_dump(),
                })
                await broadcast(pending_room, {
                    "type": "opponent_reconnected",
                    "player": user.username,
                    "color": pending_color,
                })
                logger.info(f"User {user.username} reconnected to room {pending_room.id}")
            else:
                await _set_global(user.id, ws_id, ws)
                await send_msg(ws, {"type": "auth_ok", "user_id": user.id, "username": user.username})
        else:
            await _set_global(user.id, ws_id, ws)
            await send_msg(ws, {
                "type": "auth_ok",
                "user_id": user.id,
                "username": user.username,
            })
        # Notify friends online
        await _notify_friends_online(user.id, user.username)
    except (asyncio.TimeoutError, json.JSONDecodeError, WebSocketDisconnect):
        await ws.close()
        return

    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_msg(ws, {"type": "error", "message": "无效的JSON"})
                continue

            msg_type = data.get("type", "")

            if current_room is None and user:
                found_room, found_color = room_manager.find_room_by_user_id(user.id)
                if found_room:
                    current_room = found_room
                    current_color = found_color

            if msg_type == "create_room":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                name = data.get("player_name", user.username)
                password = data.get("password", "")
                initial_time = data.get("initial_time_ms", 1800000)
                increment = data.get("increment_ms", 30000)
                room_id, color = await room_manager.create_room(
                    ws, name, password, initial_time, increment
                )
                current_room = room_manager.get_room(room_id)
                current_color = color
                current_room.black_user_id = user.id
                current_room.black_elo = user.elo
                if current_room.players["black"]:
                    current_room.players["black"].user_id = user.id
                your_title = get_title(user.elo)
                await send_msg(ws, {
                    "type": "room_created",
                    "room_id": room_id,
                    "player_color": color,
                    "has_password": bool(password),
                    "initial_time_ms": initial_time,
                    "increment_ms": increment,
                    "your_title": your_title.model_dump(),
                })

            elif msg_type == "join_room":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                room_id = data.get("room_id", "")
                name = data.get("player_name", user.username)
                password = data.get("password", "")
                color = await room_manager.join_room(room_id, ws, name, password)
                if color is None:
                    await send_msg(ws, {"type": "error", "message": "房间不存在或已满"})
                    continue
                if color == "password_required":
                    await send_msg(ws, {"type": "error", "message": "房间需要密码"})
                    continue
                current_room = room_manager.get_room(room_id)
                current_color = color
                if current_room.players["white"]:
                    current_room.players["white"].user_id = user.id
                if current_color == "white":
                    current_room.white_user_id = user.id
                    current_room.white_elo = user.elo

                opponent = current_room.players[current_room.get_opponent_color(color)]
                opp_name = opponent.name if opponent else "未知"
                opponent_elo = current_room.black_elo if color == "white" else (current_room.white_elo or 1000)

                my_title = get_title(user.elo)
                opp_title = get_title(opponent_elo)

                is_your_turn = current_room.current_turn == (game.BLACK if color == "black" else game.WHITE)

                await send_msg(ws, {
                    "type": "room_joined",
                    "room_id": room_id,
                    "player_color": color,
                    "opponent_name": opp_name,
                    "your_title": my_title.model_dump(),
                    "opponent_title": opp_title.model_dump(),
                    "board": _board_for_api(current_room.board),
                    "current_turn": _color_name(current_room.current_turn),
                    "your_turn": is_your_turn,
                    "move_history": current_room.move_history,
                })

                await broadcast(current_room, {
                    "type": "opponent_joined",
                    "player_name": name,
                    "your_color": current_room.get_opponent_color(color),
                    "player_title": my_title.model_dump(),
                    "opponent_title": opp_title.model_dump(),
                }, exclude_ws=ws)

                for c_name, player in current_room.players.items():
                    if player:
                        is_your_turn = current_room.current_turn == (game.BLACK if c_name == "black" else game.WHITE)
                        await send_msg(player.ws, {
                            "type": "game_state",
                            "board": _board_for_api(current_room.board),
                            "current_turn": _color_name(current_room.current_turn),
                            "your_turn": is_your_turn,
                            "move_history": current_room.move_history,
                        })

                # Start timer when both players have joined
                if current_room.is_full and not current_room.timer_task:
                    current_room.timer_task = asyncio.create_task(start_timer(current_room))

            elif msg_type == "place_stone":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                row = data.get("row")
                col = data.get("col")
                if row is None or col is None:
                    await send_msg(ws, {"type": "error", "message": "缺少落子坐标"})
                    continue
                result = await room_manager.handle_place_stone(current_room, current_color, row, col)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue

                # Reset timer with increment
                reset_timer(current_room)

                await broadcast(current_room, {
                    "type": "stone_placed",
                    "row": row,
                    "col": col,
                    "player": current_color,
                    "current_turn": _color_name(current_room.current_turn),
                })

                if result.get("win"):
                    current_room.timer_active = False
                    if current_room.timer_task:
                        current_room.timer_task.cancel()
                        current_room.timer_task = None
                    await broadcast(current_room, {
                        "type": "game_over",
                        "winner": result["winner"],
                        "reason": result["reason"],
                    })
                    _save_game_record(current_room)
                else:
                    for color_name, player in current_room.players.items():
                        if player:
                            await send_msg(player.ws, {
                                "type": "your_turn",
                                "your_turn": current_room.current_turn == (game.BLACK if color_name == "black" else game.WHITE),
                            })
                    asyncio.create_task(_broadcast_analysis(current_room))

            elif msg_type == "undo_request":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = await room_manager.handle_undo_request(current_room, current_color)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                opponent_color = current_room.get_opponent_color(current_color)
                opponent = current_room.players[opponent_color]
                if opponent:
                    await send_msg(opponent.ws, {"type": "undo_offered", "by": current_color})

            elif msg_type == "undo_response":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                accept = data.get("accept", False)
                result = await room_manager.handle_undo_response(current_room, current_color, accept)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                if result.get("accept"):
                    await broadcast(current_room, {
                        "type": "undo_success",
                        "board": _board_for_api(current_room.board),
                        "current_turn": _color_name(current_room.current_turn),
                        "move_history": current_room.move_history,
                    })
                else:
                    await broadcast(current_room, {
                        "type": "undo_declined",
                        "by": current_color,
                    })

            elif msg_type == "request_analysis":
                if current_room:
                    asyncio.create_task(_broadcast_analysis(current_room))

            elif msg_type == "resign":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = await room_manager.handle_resign(current_room, current_color)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                current_room.timer_active = False
                if current_room.timer_task:
                    current_room.timer_task.cancel()
                    current_room.timer_task = None
                await broadcast(current_room, {
                    "type": "game_over",
                    "winner": result["winner"],
                    "reason": result["reason"],
                })
                _save_game_record(current_room)

            elif msg_type == "draw_request":
                if not current_room or is_spectator:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = await room_manager.handle_draw_request(current_room, current_color)
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
                result = await room_manager.handle_draw_response(current_room, current_color, accept)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                if result.get("accept"):
                    current_room.timer_active = False
                    if current_room.timer_task:
                        current_room.timer_task.cancel()
                        current_room.timer_task = None
                    await broadcast(current_room, {
                        "type": "game_over",
                        "winner": None,
                        "reason": "和棋",
                    })
                    _save_game_record(current_room)
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
                        if current_room.timer_task:
                            current_room.timer_task.cancel()
                        room_manager.remove_room(current_room.id)
                    else:
                        current_room.players[current_color] = None
                    current_room = None
                    current_color = None
                    is_spectator = False

            elif msg_type == "start_match":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                if matchmaker.is_in_queue(ws_id):
                    await send_msg(ws, {"type": "error", "message": "已在匹配队列中"})
                    continue

                entry = MatchEntry(
                    user_id=user.id,
                    username=user.username,
                    elo=user.elo,
                    ws_id=ws_id,
                    joined_at=asyncio.get_event_loop().time(),
                )
                matched, other_entry = await matchmaker.add_to_queue(entry)
                if matched and other_entry:
                    await _handle_match(entry, other_entry, ws, user)
                    found_room, found_color = room_manager.find_room_by_user_id(user.id)
                    if found_room:
                        current_room = found_room
                        current_color = found_color
                else:
                    await send_msg(ws, {"type": "match_queued"})

            elif msg_type == "cancel_match":
                await matchmaker.remove_from_queue(ws_id)
                await send_msg(ws, {"type": "match_cancelled"})

            elif msg_type == "spectate_room":
                room_id = data.get("room_id", "")
                target_room = room_manager.get_room(room_id)
                if not target_room:
                    await send_msg(ws, {"type": "error", "message": "房间不存在"})
                    continue
                spec = PlayerConnection(ws, user.username)
                spec.user_id = user.id
                target_room.spectators.append(spec)
                current_room = target_room
                is_spectator = True
                await send_msg(ws, {
                    "type": "spectate_joined",
                    "room_id": room_id,
                    "board": _board_for_api(target_room.board),
                    "current_turn": _color_name(target_room.current_turn),
                    "move_history": target_room.move_history,
                    "black_name": target_room.black_name,
                    "white_name": target_room.white_name,
                    "black_title": get_title(target_room.black_elo).model_dump(),
                    "white_title": get_title(target_room.white_elo or 1000).model_dump(),
                })
                _broadcast_spectator_count(target_room)

            elif msg_type == "invite_to_room":
                to_user_id = data.get("to_user_id")
                room_id = data.get("room_id", "")
                if not to_user_id or not room_id:
                    await send_msg(ws, {"type": "error", "message": "参数不完整"})
                    continue
                target_ws = await _get_global_ws(to_user_id)
                if not target_ws:
                    await send_msg(ws, {"type": "error", "message": "对方不在线"})
                    continue
                if not current_room or current_room.id != room_id:
                    await send_msg(ws, {"type": "error", "message": "你不在该房间中"})
                    continue
                await send_msg(target_ws, {
                    "type": "room_invitation",
                    "from_user_id": user.id,
                    "from_username": user.username,
                    "room_id": room_id,
                    "black_name": current_room.black_name,
                    "white_name": current_room.white_name,
                    "game_in_progress": current_room.is_full and not current_room.game_over,
                })
                await send_msg(ws, {"type": "invite_sent", "to_user_id": to_user_id})

            elif msg_type == "chat":
                try:
                    if not current_room:
                        await send_msg(ws, {"type": "error", "message": "不在房间中"})
                        continue
                    message = data.get("message", "").strip()
                    if not message or len(message) > 500:
                        continue
                    msg_obj = ChatMessage(
                        from_user=user.username,
                        from_user_id=user.id,
                        message=message,
                        room_id=current_room.id,
                    )
                    chat_manager.add_room_message(current_room.id, msg_obj)
                    await broadcast(current_room, {
                        "type": "chat",
                        "from": user.username,
                        "from_user_id": user.id,
                        "message": message,
                    })
                except Exception as e:
                    logger.error(f"Chat handler error: {e}", exc_info=True)
                    await send_msg(ws, {"type": "error", "message": "发送消息失败"})

            elif msg_type == "global_chat":
                message = data.get("message", "").strip()
                if not message or len(message) > 500:
                    continue
                msg_obj = ChatMessage(
                    from_user=user.username,
                    from_user_id=user.id,
                    message=message,
                )
                chat_manager.add_global_message(msg_obj)
                await _broadcast_global_chat(user.username, user.id, message)

            elif msg_type == "private_chat":
                message = data.get("message", "").strip()
                to_username = data.get("to", "")
                if not message or not to_username or len(message) > 500:
                    continue
                await _send_private_chat(user.username, user.id, to_username, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user.username}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await _handle_disconnect(current_room, current_color, ws, ws_id, is_spectator, user)


async def _reconnect_timeout(room: Room, color: str, user_id: int, username: str):
    """Wait for RECONNECT_TIMEOUT seconds, then forfeit the game."""
    try:
        await asyncio.sleep(RECONNECT_TIMEOUT)
        player = room.players.get(color)
        if player and player.disconnected:
            # Forfeit - player didn't reconnect in time
            room.game_over = True
            winner_color = room.get_opponent_color(color)
            room.winner = winner_color
            room.win_reason = f"{color}超时未重连"
            room.timer_active = False
            if room.timer_task:
                room.timer_task.cancel()
                room.timer_task = None
            await broadcast(room, {
                "type": "game_over",
                "winner": winner_color,
                "reason": f"{color}超时未重连",
            })
            _save_game_record(room)
            room_manager.remove_room(room.id)
    except asyncio.CancelledError:
        pass


async def _handle_disconnect(room, color, ws, ws_id, is_spectator, user):
    if user:
        await _remove_global(user.id, ws_id)
        await _notify_friends_offline(user.id)
    await matchmaker.remove_from_queue(ws_id)
    if room:
        if is_spectator:
            room.spectators = [s for s in getattr(room, "spectators", []) if s.ws != ws]
            _broadcast_spectator_count(room)
        else:
            player = room.players.get(color) if color else None
            if player:
                player.disconnected = True
                player.ws = None

            opponent_color = room.get_opponent_color(color) if color else None
            opponent = room.players[opponent_color] if opponent_color else None
            if opponent:
                asyncio.create_task(send_msg(opponent.ws, {
                    "type": "opponent_disconnected",
                    "message": "对手断线了，等待重连中...",
                }))

            # Start reconnect timeout if game was in progress
            if room.is_full:
                task = asyncio.create_task(_reconnect_timeout(
                    room, color, user.id if user else 0, user.username if user else "unknown"
                ))
                if player:
                    player.reconnect_task = task
            else:
                if room.player_count <= 1:
                    if room.timer_task:
                        room.timer_task.cancel()
                    room_manager.remove_room(room.id)
                else:
                    room.players[color] = None


async def _handle_match(entry: MatchEntry, other_entry: MatchEntry, ws: WebSocket, user: User):
    """Create a room for the matched pair, notify both players."""

    # Create room with both players
    other_ws = await _get_global_ws(other_entry.user_id)
    if not other_ws:
        await send_msg(ws, {"type": "error", "message": "对手已离线"})
        return

    room_id, _ = await room_manager.create_room(ws, user.username)
    room = room_manager.get_room(room_id)
    room.black_user_id = user.id
    room.black_elo = user.elo
    room.black_name = user.username
    if room.players["black"]:
        room.players["black"].user_id = user.id

    # Join the other player as white
    color = await room_manager.join_room(room_id, other_ws, other_entry.username)
    if color != "white":
        await send_msg(ws, {"type": "error", "message": "匹配房间创建失败"})
        room_manager.remove_room(room_id)
        return

    room.white_user_id = other_entry.user_id
    room.white_elo = other_entry.elo
    if room.players["white"]:
        room.players["white"].user_id = other_entry.user_id

    # Notify both
    my_title = get_title(user.elo)
    opp_title = get_title(other_entry.elo)
    await send_msg(ws, {
        "type": "match_found",
        "room_id": room_id,
        "opponent": {"name": other_entry.username, "elo": other_entry.elo, "title": opp_title.model_dump()},
        "your_color": "black",
        "your_title": my_title.model_dump(),
        "board": _board_for_api(room.board),
        "current_turn": _color_name(room.current_turn),
        "your_turn": room.current_turn == game.BLACK,
        "move_history": room.move_history,
    })
    await send_msg(other_ws, {
        "type": "match_found",
        "room_id": room_id,
        "opponent": {"name": user.username, "elo": user.elo, "title": my_title.model_dump()},
        "your_color": "white",
        "your_title": opp_title.model_dump(),
        "board": _board_for_api(room.board),
        "current_turn": _color_name(room.current_turn),
        "your_turn": room.current_turn == game.WHITE,
        "move_history": room.move_history,
    })

    for color_name, player in room.players.items():
        if player:
            is_your_turn = room.current_turn == (game.BLACK if color_name == "black" else game.WHITE)
            await send_msg(player.ws, {
                "type": "game_state",
                "board": _board_for_api(room.board),
                "current_turn": _color_name(room.current_turn),
                "your_turn": is_your_turn,
                "move_history": room.move_history,
            })
    if not room.timer_task:
        room.timer_task = asyncio.create_task(start_timer(room))


def _save_game_record(room):
    asyncio.create_task(_async_save_game(room))


async def _async_save_game(room):
    try:
        black_id = getattr(room, "black_user_id", None)
        white_id = getattr(room, "white_user_id", None)
        if not black_id or not white_id:
            return
        from ..services.game_service import save_game
        async with async_session_factory() as db:
            moves = [
                {"row": m["row"], "col": m["col"], "player": m["player"]}
                for m in room.move_history
            ]
            await save_game(
                db=db,
                black_id=black_id,
                white_id=white_id,
                winner=room.winner,
                reason=room.win_reason,
                moves=moves,
            )
    except Exception as e:
        logger.error(f"Failed to save game: {e}")


async def _broadcast_analysis(room):
    analysis_result = await request_analysis(room.board)
    if analysis_result:
        await broadcast(room, {"type": "analysis_result", "analysis": analysis_result})


def _broadcast_spectator_count(room):
    count = len(getattr(room, "spectators", []))
    asyncio.create_task(broadcast(room, {"type": "spectator_count", "count": count}))


def _board_for_api(board):
    return [
        ["black" if cell == game.BLACK else "white" if cell == game.WHITE else None for cell in row]
        for row in board
    ]


def _color_name(player: int) -> str:
    return "black" if player == game.BLACK else "white"
