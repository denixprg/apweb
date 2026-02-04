from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, schemas
from .deps import get_db, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/invites", response_model=schemas.InviteOut)
def create_invite(payload: schemas.InviteCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    invite = crud.create_invite(db, payload.expires_in_days)
    return schemas.InviteOut(code=invite.code, expires_at=invite.expires_at)


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return crud.list_users(db)


@router.post("/users/{user_id}/block", response_model=schemas.UserOut)
def block_user(user_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = crud.block_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/unblock", response_model=schemas.UserOut)
def unblock_user(user_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = crud.unblock_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
