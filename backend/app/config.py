import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    # Database
    _db_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./gomoku.db",
    )

    @property
    def DATABASE_URL(self) -> str:
        # Render PostgreSQL URL (postgresql://...) -> SQLAlchemy async format
        url = self._db_url
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ELO
    ELO_K: int = 32
    ELO_INITIAL: int = 1000

    # Server
    WS_HOST: str = os.getenv("WS_HOST", "0.0.0.0")
    WS_PORT: int = int(os.getenv("WS_PORT", "8000"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")


settings = Settings()
