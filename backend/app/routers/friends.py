from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..models.friend import Friendship, FriendRequest
from ..models import FriendListResponse, FriendEntry
from ..services.auth_service import verify_token
from ..services.title_service import get_title

router = APIRouter(prefix="/api/friends", tags=["friends"])


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


@router.get("/", response_model=FriendListResponse)
async def get_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Friendship).where(Friendship.user_id == current_user.id)
    )
    friendships = list(result.scalars().all())

    friend_ids = [f.friend_id for f in friendships]
    entries = []
    if friend_ids:
        result = await db.execute(select(User).where(User.id.in_(friend_ids)))
        friends = list(result.scalars().all())
        entries = [
            FriendEntry(id=f.id, username=f.username, nickname=f.nickname, elo=f.elo, title=get_title(f.elo))
            for f in friends
        ]

    return FriendListResponse(friends=entries)


@router.get("/pending")
async def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.to_user_id == current_user.id,
            FriendRequest.status == "pending",
        )
    )
    requests = list(result.scalars().all())
    entries = []
    for req in requests:
        user_result = await db.execute(select(User).where(User.id == req.from_user_id))
        from_user = user_result.scalar_one_or_none()
        if from_user:
            entries.append({
                "request_id": req.id,
                "from_user_id": from_user.id,
                "from_username": from_user.username,
                "from_nickname": from_user.nickname,
                "created_at": str(req.created_at),
            })
    return {"requests": entries}


@router.get("/search")
async def search_users(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.username.ilike(f"%{q}%"),
            User.id != current_user.id,
        ).limit(20)
    )
    users = list(result.scalars().all())
    return {"users": [
        {"id": u.id, "username": u.username, "nickname": u.nickname, "elo": u.elo, "title": get_title(u.elo).model_dump()}
        for u in users
    ]}


@router.post("/request")
async def send_friend_request(
    to_username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == to_username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    existing = await db.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.user_id == current_user.id, Friendship.friend_id == target.id),
                and_(Friendship.friend_id == current_user.id, Friendship.user_id == target.id),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="已是好友")

    pending = await db.execute(
        select(FriendRequest).where(
            FriendRequest.from_user_id == current_user.id,
            FriendRequest.to_user_id == target.id,
            FriendRequest.status == "pending",
        )
    )
    if pending.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="已发送过好友申请")

    req = FriendRequest(from_user_id=current_user.id, to_user_id=target.id)
    db.add(req)
    await db.commit()
    return {"ok": True, "message": "好友申请已发送"}


@router.post("/respond")
async def respond_friend_request(
    request_id: int,
    accept: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = await db.get(FriendRequest, request_id)
    if not req or req.to_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="请求不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="请求已处理")

    if accept:
        req.status = "accepted"
        friendship = Friendship(user_id=req.from_user_id, friend_id=req.to_user_id)
        friendship2 = Friendship(user_id=req.to_user_id, friend_id=req.from_user_id)
        db.add(friendship)
        db.add(friendship2)
    else:
        req.status = "rejected"

    await db.commit()
    return {"ok": True, "message": "已接受" if accept else "已拒绝"}


@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.user_id == current_user.id, Friendship.friend_id == friend_id),
                and_(Friendship.friend_id == current_user.id, Friendship.user_id == friend_id),
            )
        )
    )
    friendships = list(result.scalars().all())
    for f in friendships:
        await db.delete(f)
    await db.commit()
    return {"ok": True, "message": "好友已删除"}
