from .auth import router as auth_router
from .users import router as users_router
from .games import router as games_router
from .friends import router as friends_router
from .admin import router as admin_router

__all__ = ["auth_router", "users_router", "games_router", "friends_router", "admin_router"]
