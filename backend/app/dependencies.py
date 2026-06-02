from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .models.user import User
from .services.auth_service import verify_token


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


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问，需要管理员权限")
    return current_user
