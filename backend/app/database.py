from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        from .models.user import User
        from .models.game import GameRecord
        from .models.friend import Friendship, FriendRequest
        await conn.run_sync(Base.metadata.create_all)
        # Migration: add new columns if missing
        from sqlalchemy import inspect, text
        def _migrate(sync_conn):
            inspector = inspect(sync_conn)
            columns = [c["name"] for c in inspector.get_columns("users")]
            if "board_image" not in columns:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN board_image VARCHAR(512) NOT NULL DEFAULT ''"))
            if "background_image" not in columns:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN background_image VARCHAR(512) NOT NULL DEFAULT ''"))
        await conn.run_sync(_migrate)
