from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..models import GameRecordResponse, GameHistoryResponse
from ..services.auth_service import verify_token
from ..services.game_service import get_user_games

router = APIRouter(prefix="/api/games", tags=["games"])


async def get_current_user(
    authorization: str = Header(""),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证信息")
    token = authorization[7:]
    user_id = verify_token(token, "access")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的令牌")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="账号已被封禁")
    return user


@router.get("/", response_model=GameHistoryResponse)
async def get_game_history(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records, total = await get_user_games(db, current_user.id, page, limit)
    games = []
    for r in records:
        games.append(GameRecordResponse(
            id=r.id,
            black_id=r.black_id,
            white_id=r.white_id,
            winner=r.winner,
            reason=r.reason,
            moves_json=r.moves_json,
            black_elo_change=r.black_elo_change,
            white_elo_change=r.white_elo_change,
            started_at=str(r.started_at),
            ended_at=str(r.ended_at) if r.ended_at else None,
        ))
    return GameHistoryResponse(games=games, total=total, page=page)


@router.get("/{game_id}", response_model=GameRecordResponse)
async def get_game_detail(
    game_id: int,
    db: AsyncSession = Depends(get_db),
):
    from ..models.game import GameRecord
    record = await db.get(GameRecord, game_id)
    if not record:
        raise HTTPException(status_code=404, detail="对局不存在")
    return GameRecordResponse(
        id=record.id,
        black_id=record.black_id,
        white_id=record.white_id,
        winner=record.winner,
        reason=record.reason,
        moves_json=record.moves_json,
        black_elo_change=record.black_elo_change,
        white_elo_change=record.white_elo_change,
        started_at=str(record.started_at),
        ended_at=str(record.ended_at) if record.ended_at else None,
    )
