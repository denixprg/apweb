from __future__ import annotations

import time
from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from .database import SessionLocal
from .auth import decode_access_token
from .models import User

_RATE_LIMIT = {}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def rate_limit(request: Request, key_prefix: str = "auth", max_per_minute: int = 20) -> None:
    ip = request.client.host if request.client else "unknown"
    key = f"{key_prefix}:{ip}"
    now = int(time.time())
    window = now // 60
    bucket = _RATE_LIMIT.get(key)
    if not bucket or bucket[0] != window:
        _RATE_LIMIT[key] = (window, 1)
        return
    count = bucket[1] + 1
    _RATE_LIMIT[key] = (window, count)
    if count > max_per_minute:
        raise HTTPException(status_code=429, detail="Too many requests")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(decode_access_token)) -> User:
    user = db.query(User).filter(User.id == token.user_id).first()
    if not user or user.is_blocked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
