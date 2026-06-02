import datetime
import hashlib
import secrets
import bcrypt as _bcrypt
from jose import jwt, JWTError
from ..config import settings


def hash_password(password: str) -> str:
    pre_hashed = hashlib.sha256(password.encode()).hexdigest()
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(pre_hashed.encode(), salt).decode()


def verify_password(password: str, password_hash: str) -> bool:
    pre_hashed = hashlib.sha256(password.encode()).hexdigest()
    return _bcrypt.checkpw(pre_hashed.encode(), password_hash.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> int | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            return None
        return int(payload.get("sub", 0))
    except (JWTError, ValueError, TypeError):
        return None


def generate_csrf_token() -> str:
    return secrets.token_hex(32)
