# =============================================================
# api/auth/security.py — JWT et tokens de rafraîchissement
# =============================================================

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config import (
    JWT_ACCESS_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_EXPIRE_DAYS,
    JWT_SECRET,
)


def create_access_token(*, user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
