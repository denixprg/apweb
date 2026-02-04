from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List
import secrets
from sqlalchemy.orm import Session

from . import models
from .auth import get_password_hash


def create_user(db: Session, username: str, password: str, is_admin: bool = False) -> models.User:
    user = models.User(username=username, password_hash=get_password_hash(password), is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user(db: Session, user_id) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_invite(db: Session, expires_in_days: Optional[int]) -> models.Invite:
    code = secrets.token_urlsafe(8)
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    invite = models.Invite(code=code, expires_at=expires_at)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def use_invite(db: Session, code: str, user_id) -> bool:
    invite = db.query(models.Invite).filter(models.Invite.code == code).first()
    if not invite:
        return False
    if invite.used_by_user_id:
        return False
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        return False
    invite.used_by_user_id = user_id
    db.add(invite)
    db.commit()
    return True


def list_users(db: Session) -> List[models.User]:
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


def block_user(db: Session, user_id) -> Optional[models.User]:
    user = get_user(db, user_id)
    if not user:
        return None
    user.is_blocked = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def unblock_user(db: Session, user_id) -> Optional[models.User]:
    user = get_user(db, user_id)
    if not user:
        return None
    user.is_blocked = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_item(db: Session, code: str, name: str) -> models.Item:
    item = models.Item(code=code, name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: models.Item, code: Optional[str], name: Optional[str]) -> models.Item:
    if code:
        item.code = code
    if name:
        item.name = name
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_items(db: Session) -> List[models.Item]:
    return db.query(models.Item).order_by(models.Item.created_at.desc()).all()


def get_item(db: Session, item_id) -> Optional[models.Item]:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def create_rating(db: Session, item_id, user_id, a: int, b: int, c: int, d: int, n: int) -> models.Rating:
    rating = models.Rating(item_id=item_id, user_id=user_id, a=a, b=b, c=c, d=d, n=n)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating
