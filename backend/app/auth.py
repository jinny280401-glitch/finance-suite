from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db, User


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def _candidate_tokens(request: Request) -> list[str]:
    """Return every access token the browser sent, preserving duplicates."""
    tokens: list[str] = []

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        tokens.append(cookie_token)

    raw_cookie = request.headers.get("cookie", "")
    for part in raw_cookie.split(";"):
        name, _, value = part.strip().partition("=")
        if name == "access_token" and value and value not in tokens:
            tokens.append(value)

    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        bearer = auth_header[7:].strip()
        if bearer and bearer not in tokens:
            tokens.append(bearer)

    return tokens


def _user_from_token(token: str, db: Session) -> Optional[User]:
    payload = verify_token(token)
    if payload is None:
        return None

    user_id = payload.get("user_id")
    if user_id is None:
        return None

    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI dependency: extract and validate current user from auth tokens."""
    tokens = _candidate_tokens(request)
    if not tokens:
        raise HTTPException(status_code=401, detail="未登录，请先登录")

    for token in tokens:
        user = _user_from_token(token, db)
        if user:
            return user

    raise HTTPException(status_code=401, detail="登录已过期，请重新登录")


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """FastAPI dependency: get current user or None (no error if not logged in)."""
    for token in _candidate_tokens(request):
        user = _user_from_token(token, db)
        if user:
            return user
    return None
