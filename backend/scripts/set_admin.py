"""
Usage: python scripts/set_admin.py <username>

Set or unset a user as admin.
Use --remove to revoke admin privilege.
"""
import sys
import asyncio
import os
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.database import async_session_factory, init_db
from app.models.user import User
from sqlalchemy import select


async def main():
    args = sys.argv[1:]
    remove = "--remove" in args
    if remove:
        args.remove("--remove")

    if len(args) < 1:
        print("用法: python scripts/set_admin.py [--remove] <用户名>")
        sys.exit(1)

    username = args[0]
    await init_db()

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            sys.exit(1)

        if remove:
            user.is_admin = 0
            action = "取消"
        else:
            user.is_admin = 1
            action = "设置"

        await db.commit()
        print(f"[OK] 已{action}用户 '{username}' (id={user.id}) 为管理员")


if __name__ == "__main__":
    asyncio.run(main())
