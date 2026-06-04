from pydantic import BaseModel
from fastapi import APIRouter
from .room_manager import cc_room_manager
from . import game
from .ai_analysis import request_ai_move

router = APIRouter(prefix="/api/cc")


class CcAiMoveRequest(BaseModel):
    board: list
    color: str  # "red" or "black"
    api_key: str | None = None


class CcAiMoveResponse(BaseModel):
    from_row: int
    from_col: int
    to_row: int
    to_col: int


@router.get("/rooms")
async def list_rooms():
    return cc_room_manager.list_open_rooms()


@router.get("/rooms/active")
async def list_active_rooms():
    return cc_room_manager.list_spectatable_rooms()


@router.post("/ai-move", response_model=CcAiMoveResponse)
async def ai_move(req: CcAiMoveRequest):
    board = game.api_to_board(req.board)
    result = await request_ai_move(board, req.api_key, req.color)
    if result:
        return CcAiMoveResponse(**result)
    return CcAiMoveResponse(from_row=-1, from_col=-1, to_row=-1, to_col=-1)
