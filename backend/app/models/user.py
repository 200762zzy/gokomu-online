import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    nickname: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    avatar_url: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    board_image: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    background_image: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    elo: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    is_admin: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)
    is_banned: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
