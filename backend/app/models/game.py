import datetime
from sqlalchemy import String, Integer, DateTime, Text, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class GameRecord(Base):
    __tablename__ = "game_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    black_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    white_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    winner: Mapped[str | None] = mapped_column(String(8), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    moves_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    black_elo_before: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    white_elo_before: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    black_elo_change: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    white_elo_change: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reviews_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
