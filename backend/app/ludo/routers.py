import json, asyncio, logging
from fastapi import WebSocket, WebSocketDisconnect
from .room_manager import manager as ludo_manager
from ..services.auth_service import verify_token
from ..ws.handler import register_global_connection, unregister_global_connection, notify_friends_online, notify_friends_offline

logger = logging.getLogger(__name__)

_ludo_ws_counter = 0


async def send_msg(ws: WebSocket, data: dict):
    try:
        await ws.send_json(data)
    except Exception:
        pass


async def handle_ludo_websocket(ws: WebSocket):
    await ws.accept()
    global _ludo_ws_counter
    _ludo_ws_counter += 1
    ws_id = _ludo_ws_counter

    user_id = None
    username = None
    current_room = None
    current_player_idx = None

    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=10.0)
        data = json.loads(raw)
        if data.get("type") == "auth":
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

            if msg_type == "create_room":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                name = data.get("player_name", username)
                room = await ludo_manager.create_room(ws, name, "", user_id)
                current_room = room
                current_player_idx = 0

            elif msg_type == "join_room":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                room_id = data.get("room_id", "")
                name = data.get("player_name", username)
                room = ludo_manager.get_room(room_id)
                if not room:
                    await send_msg(ws, {"type": "error", "message": "房间不存在"})
                    continue
                if room.is_full():
                    await send_msg(ws, {"type": "error", "message": "房间已满"})
                    continue
                await ludo_manager.join_room(ws, room_id, name, "", user_id)
                _, player_idx = room.find_player_by_user_id(user_id)
                if player_idx is not None:
                    current_room = room
                    current_player_idx = player_idx

            elif msg_type in ("roll_dice", "move_piece", "chat"):
                if current_room and current_player_idx is not None:
                    await ludo_manager.handle_message(current_room, current_player_idx, data)
                else:
                    await send_msg(ws, {"type": "error", "message": "你不在房间中"})

            elif msg_type == "leave_room":
                if current_room and current_player_idx is not None:
                    await ludo_manager.handle_message(current_room, current_player_idx, data)
                current_room = None
                current_player_idx = None

            elif msg_type == "ping":
                await send_msg(ws, {"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Ludo WS disconnected (user={username})")
    except Exception as e:
        logger.error(f"Ludo WS error: {e}")
    finally:
        if current_room and current_player_idx is not None:
            await ludo_manager.handle_disconnect(current_room, current_player_idx)
        if user_id:
            unregister_global_connection(user_id, ws_id)
            notify_friends_offline(user_id)
