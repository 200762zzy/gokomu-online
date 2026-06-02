from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.auth_service import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from ..services.title_service import get_title
from ..models import AuthRegisterRequest, AuthLoginRequest, AuthTokenResponse, AuthRefreshRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
async def register(req: AuthRegisterRequest, db: AsyncSession = Depends(get_db)):
    if len(req.username) < 2 or len(req.username) > 24:
        raise HTTPException(status_code=400, detail="用户名长度需在2-24字符之间")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")

    try:
        result = await db.execute(select(User).where(User.username == req.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="用户名已被注册")

        user = User(
            username=req.username,
            password_hash=hash_password(req.password),
            nickname=req.nickname or req.username,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return AuthTokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            user_id=user.id,
            username=user.username,
            nickname=user.nickname,
            elo=user.elo,
            is_admin=bool(user.is_admin),
            title=get_title(user.elo),
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"注册失败: {e}")
        raise HTTPException(status_code=400, detail=f"注册失败：{str(e)}")


@router.post("/login", response_model=AuthTokenResponse)
async def login(req: AuthLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="账号已被封禁")

    return AuthTokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        elo=user.elo,
        title=get_title(user.elo),
    )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(req: AuthRefreshRequest, db: AsyncSession = Depends(get_db)):
    user_id = verify_token(req.refresh_token, "refresh")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="账号已被封禁")

    return AuthTokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        elo=user.elo,
        title=get_title(user.elo),
    )
