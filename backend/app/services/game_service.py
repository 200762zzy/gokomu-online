import json
import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.game import GameRecord
from ..models.user import User
from .elo_service import calculate_elo


async def save_game(
    db: AsyncSession,
    black_id: int,
    white_id: int,
    winner: str | None,
    reason: str | None,
    moves: list[dict],
    reviews: list[dict] | None = None,
    game_type: str = "gomoku",
) -> GameRecord:
    black_user = await db.get(User, black_id)
    white_user = await db.get(User, white_id)
    if not black_user or not white_user:
        raise ValueError("Player not found")

    black_elo_before = black_user.elo
    white_elo_before = white_user.elo

    if winner == "black":
        score_a = 1.0
    elif winner == "white":
        score_a = 0.0
    else:
        score_a = 0.5

    new_black_elo, new_white_elo = calculate_elo(black_elo_before, white_elo_before, score_a)

    black_user.elo = new_black_elo
    white_user.elo = new_white_elo

    record = GameRecord(
        game_type=game_type,
        black_id=black_id,
        white_id=white_id,
        winner=winner,
        reason=reason,
        moves_json=json.dumps(moves, ensure_ascii=False),
        black_elo_before=black_elo_before,
        white_elo_before=white_elo_before,
        black_elo_change=new_black_elo - black_elo_before,
        white_elo_change=new_white_elo - white_elo_before,
        reviews_json=json.dumps(reviews or [], ensure_ascii=False),
        ended_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_user_games(
    db: AsyncSession, user_id: int, page: int = 1, limit: int = 20,
    game_type: str | None = None,
) -> tuple[list[GameRecord], int]:
    offset = (page - 1) * limit
    conditions = (GameRecord.black_id == user_id) | (GameRecord.white_id == user_id)
    if game_type:
        conditions = (GameRecord.game_type == game_type) & conditions
    query = (
        select(GameRecord)
        .where(conditions)
        .order_by(GameRecord.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    games = list(result.scalars().all())

    count_query = select(func.count()).select_from(GameRecord).where(conditions)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return games, total


async def get_leaderboard(
    db: AsyncSession, page: int = 1, limit: int = 100
) -> tuple[list[User], int]:
    offset = (page - 1) * limit
    query = (
        select(User)
        .where(User.is_banned == 0)
        .order_by(User.elo.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    users = list(result.scalars().all())

    count_query = select(func.count()).select_from(User).where(User.is_banned == 0)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return users, total
