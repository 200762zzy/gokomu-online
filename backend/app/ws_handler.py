import json
import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from .room_manager import RoomManager, Room
from .ai_analysis import request_analysis

logger = logging.getLogger(__name__)

DISCONNECT_TIMEOUT = 60


async def send_msg(ws: WebSocket, msg: dict):
    try:
        await ws.send_json(msg)
    except Exception:
        pass


async def broadcast(room: Room, msg: dict, exclude: WebSocket | None = None):
    for player in room.players.values():
        if player and player.ws != exclude:
            await send_msg(player.ws, msg)


async def handle_websocket(ws: WebSocket, manager: RoomManager):
    await ws.accept()
    logger.info("New WebSocket connection")

    current_room: Room | None = None
    current_color: str | None = None
    player_name: str | None = None

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
                name = data.get("player_name", "玩家")
                room_id, color = await manager.create_room(ws, name)
                current_room = manager.get_room(room_id)
                current_color = color
                player_name = name
                await send_msg(ws, {
                    "type": "room_created",
                    "room_id": room_id,
                    "player_color": color,
                })
                logger.info(f"Room {room_id} created by {name}")

            elif msg_type == "join_room":
                if current_room:
                    await send_msg(ws, {"type": "error", "message": "你已在房间中"})
                    continue
                room_id = data.get("room_id", "")
                name = data.get("player_name", "玩家")
                color = await manager.join_room(room_id, ws, name)
                if color is None:
                    await send_msg(ws, {"type": "error", "message": "房间不存在或已满"})
                    continue
                current_room = manager.get_room(room_id)
                current_color = color
                player_name = name

                opponent = current_room.players[current_room.get_opponent_color(color)]
                opp_name = opponent.name if opponent else "未知"

                await send_msg(ws, {
                    "type": "room_joined",
                    "room_id": room_id,
                    "player_color": color,
                    "opponent_name": opp_name,
                })

                opponent_ws = opponent.ws if opponent else None
                await broadcast(current_room, {
                    "type": "opponent_joined",
                    "player_name": name,
                    "your_color": current_room.get_opponent_color(color),
                }, exclude=ws)

                await broadcast(current_room, {
                    "type": "game_state",
                    "board": _board_for_api(current_room.board),
                    "current_turn": _color_name(current_room.current_turn),
                    "your_turn": current_room.current_turn == game.BLACK,
                    "move_history": current_room.move_history,
                })

            elif msg_type == "place_stone":
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                row = data.get("row")
                col = data.get("col")
                if row is None or col is None:
                    await send_msg(ws, {"type": "error", "message": "缺少落子坐标"})
                    continue
                result = await manager.handle_place_stone(current_room, current_color, row, col)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue

                await broadcast(current_room, {
                    "type": "stone_placed",
                    "row": row,
                    "col": col,
                    "player": current_color,
                    "current_turn": _color_name(current_room.current_turn),
                    "your_turn": None,
                })

                if result.get("win"):
                    await broadcast(current_room, {
                        "type": "game_over",
                        "winner": result["winner"],
                        "reason": result["reason"],
                    })
                else:
                    for color_name, player in current_room.players.items():
                        if player:
                            await send_msg(player.ws, {
                                "type": "your_turn",
                                "your_turn": current_room.current_turn == (game.BLACK if color_name == "black" else game.WHITE),
                            })
                    asyncio.create_task(_broadcast_analysis(current_room))

            elif msg_type == "undo_request":
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = await manager.handle_undo_request(current_room, current_color)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                opponent_color = current_room.get_opponent_color(current_color)
                opponent = current_room.players[opponent_color]
                if opponent:
                    await send_msg(opponent.ws, {
                        "type": "undo_offered",
                        "by": current_color,
                    })

            elif msg_type == "undo_response":
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                accept = data.get("accept", False)
                result = await manager.handle_undo_response(current_room, current_color, accept)
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
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = await manager.handle_resign(current_room, current_color)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                await broadcast(current_room, {
                    "type": "game_over",
                    "winner": result["winner"],
                    "reason": result["reason"],
                })

            elif msg_type == "draw_request":
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                result = await manager.handle_draw_request(current_room, current_color)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                opponent_color = current_room.get_opponent_color(current_color)
                opponent = current_room.players[opponent_color]
                if opponent:
                    await send_msg(opponent.ws, {
                        "type": "draw_offered",
                        "by": current_color,
                    })

            elif msg_type == "draw_response":
                if not current_room:
                    await send_msg(ws, {"type": "error", "message": "未加入房间"})
                    continue
                accept = data.get("accept", False)
                result = await manager.handle_draw_response(current_room, current_color, accept)
                if not result["ok"]:
                    await send_msg(ws, {"type": "error", "message": result["error"]})
                    continue
                if result.get("accept"):
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
                    if current_room.player_count <= 1:
                        manager.remove_room(current_room.id)
                    else:
                        current_room.players[current_color] = None
                    current_room = None
                    current_color = None

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {player_name}")
        if current_room:
            opponent_color = current_room.get_opponent_color(current_color)
            opponent = current_room.players[opponent_color]
            if opponent:
                await send_msg(opponent.ws, {
                    "type": "opponent_disconnected",
                    "message": "对手断线了",
                })
            if current_room.player_count <= 1:
                manager.remove_room(current_room.id)
            else:
                current_room.players[current_color] = None
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if current_room:
            manager.remove_room(current_room.id)


from . import game


def _board_for_api(board: list[list[int]]) -> list[list[str | None]]:
    return [
        ["black" if cell == game.BLACK else "white" if cell == game.WHITE else None for cell in row]
        for row in board
    ]


def _color_name(player: int) -> str:
    return "black" if player == game.BLACK else "white"


async def _broadcast_analysis(room: Room):
    analysis_result = await request_analysis(room.board)
    if analysis_result:
        await broadcast(room, {
            "type": "analysis_result",
            "analysis": analysis_result,
        })
