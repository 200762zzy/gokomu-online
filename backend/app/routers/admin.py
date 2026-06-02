import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.user import User
from ..models.friend import Friendship, FriendRequest
from ..models.game import GameRecord
from ..room_manager import room_manager
from ..dependencies import require_admin
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


class SetAdminRequest(BaseModel):
    user_id: int
    is_admin: bool


class BanRequest(BaseModel):
    user_id: int
    is_banned: bool


class SetEloRequest(BaseModel):
    user_id: int
    elo: int


@router.get("/users")
async def list_all_users(
    page: int = 1,
    page_size: int = 50,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(User))
    total_users = total_result.scalars().all()
    total_count = len(total_users)

    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).order_by(User.id).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "elo": u.elo,
                "is_banned": bool(u.is_banned),
                "is_admin": bool(u.is_admin),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.post("/set-admin")
async def set_admin(
    req: SetAdminRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if req.user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的管理员状态")
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_admin = 1 if req.is_admin else 0
    await db.commit()
    return {"message": f"用户 {user.username} 管理员状态已设置为 {req.is_admin}"}


@router.post("/ban")
async def ban_user(
    req: BanRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if req.user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能封禁自己")
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_banned = 1 if req.is_banned else 0
    await db.commit()

    if req.is_banned:
        room_manager.kick_user_from_rooms(req.user_id, "你的账号已被封禁")

    action = "封禁" if req.is_banned else "解封"
    return {"message": f"用户 {user.username} 已{action}"}


@router.post("/delete-user")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.execute(
        delete(Friendship).where(
            (Friendship.user_id == user_id) | (Friendship.friend_id == user_id)
        )
    )
    await db.execute(
        delete(FriendRequest).where(
            (FriendRequest.from_user_id == user_id) | (FriendRequest.to_user_id == user_id)
        )
    )
    await db.execute(
        delete(GameRecord).where(
            (GameRecord.black_id == user_id) | (GameRecord.white_id == user_id)
        )
    )
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    room_manager.kick_user_from_rooms(user_id, "你的账号已被删除")
    return {"message": f"用户 {user.username} 已删除"}


@router.get("/rooms")
async def list_admin_rooms(admin: User = Depends(require_admin)):
    rooms = room_manager.list_all_rooms()
    return {
        "rooms": [
            {
                "room_id": r.id,
                "player_count": r.player_count,
                "spectator_count": len(r.spectators),
                "players": [
                    {"user_id": p.user_id, "username": p.name}
                    for p in r.players.values()
                    if p
                ],
                "is_gaming": not r.game_over and r.player_count == 2,
            }
            for r in rooms
        ]
    }


@router.post("/close-room")
async def close_room(
    room_id: str,
    admin: User = Depends(require_admin),
):
    room_manager.close_room(room_id, "管理员已关闭该房间")
    return {"message": f"房间 {room_id} 已关闭"}


@router.get("/logs")
async def get_logs(
    lines: int = 100,
    level: str = None,
    admin: User = Depends(require_admin),
):
    from ..log_handler import log_buffer
    logs = log_buffer.get_logs(lines)
    if level:
        logs = [l for l in logs if l["level"] == level.upper()]
    return {"logs": logs}


@router.post("/set-elo")
async def set_elo(
    req: SetEloRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    old_elo = user.elo
    user.elo = req.elo
    await db.commit()
    return {"message": f"用户 {user.username} ELO 已从 {old_elo} 调整为 {req.elo}"}
