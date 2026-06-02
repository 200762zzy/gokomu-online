from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..models import UserProfileResponse, LeaderboardResponse, LeaderboardEntry
from ..services.game_service import get_leaderboard, get_user_games
from ..services.title_service import get_title
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        board_image=current_user.board_image,
        background_image=current_user.background_image,
        elo=current_user.elo,
        is_admin=bool(current_user.is_admin),
        created_at=str(current_user.created_at),
        title=get_title(current_user.elo),
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    nickname: str = "",
    avatar_url: str = "",
    board_image: str = "",
    background_image: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if nickname:
        current_user.nickname = nickname
    if avatar_url:
        current_user.avatar_url = avatar_url
    if board_image:
        current_user.board_image = board_image
    if background_image:
        current_user.background_image = background_image
    await db.commit()
    await db.refresh(current_user)
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        board_image=current_user.board_image,
        background_image=current_user.background_image,
        elo=current_user.elo,
        is_admin=bool(current_user.is_admin),
        created_at=str(current_user.created_at),
        title=get_title(current_user.elo),
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def leaderboard(page: int = 1, limit: int = 100, db: AsyncSession = Depends(get_db)):
    users, total = await get_leaderboard(db, page, limit)
    entries = [
        LeaderboardEntry(
            id=u.id,
            username=u.username,
            nickname=u.nickname,
            elo=u.elo,
            rank=offset + 1,
            title=get_title(u.elo),
        )
        for offset, u in enumerate(users)
    ]
    return LeaderboardResponse(entries=entries, total=total, page=page)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        elo=user.elo,
        is_admin=bool(user.is_admin),
        created_at=str(user.created_at),
        title=get_title(user.elo),
    )
