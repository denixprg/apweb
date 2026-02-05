from __future__ import annotations

import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine
from . import models, schemas, crud, stats
from .auth import verify_password, create_access_token
from .deps import get_db, get_current_user, require_admin, rate_limit
from .admin import router as admin_router
from .bootstrap import ensure_bootstrap_users

app = FastAPI(title="Rating App API")

# CORS (solo afecta a navegadores; la app Kivy no lo necesita, pero no molesta)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)


# ✅ Ruta raíz para que el dominio no devuelva {"detail":"Not Found"}
@app.get("/")
def root():
    return {"status": "ok", "service": "Rating App API"}


# ✅ Healthcheck útil para Render/monitoreo
@app.get("/health")
def health():
    return {"ok": True}


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        ensure_bootstrap_users(db)
    finally:
        db.close()


@app.post("/auth/register", response_model=schemas.UserOut)
def register(payload: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, key_prefix="auth")
    if crud.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    user = crud.create_user(db, payload.username, payload.password, is_admin=False)
    if not crud.use_invite(db, payload.invite_code, user.id):
        raise HTTPException(status_code=400, detail="Invalid invite code")
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, key_prefix="auth")
    user = crud.get_user_by_username(db, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_blocked:
        raise HTTPException(status_code=401, detail="User blocked")
    token = create_access_token(str(user.id))
    return schemas.Token(access_token=token)


@app.get("/me", response_model=schemas.MeOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@app.get("/items", response_model=list[schemas.ItemOut])
def list_items(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return crud.list_items(db)


@app.post("/items", response_model=schemas.ItemOut)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.create_item(db, payload.code, payload.name)


@app.patch("/items/{item_id}", response_model=schemas.ItemOut)
def update_item(item_id: str, payload: schemas.ItemUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.update_item(db, item, payload.code, payload.name)


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="ADMIN_ONLY")
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return None


@app.post("/items/{item_id}/ratings", response_model=schemas.RatingOut)
def rate_item(item_id: str, payload: schemas.RatingCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    last_rating = (
        db.query(models.Rating)
        .filter(models.Rating.item_id == item_id, models.Rating.user_id == user.id)
        .order_by(models.Rating.created_at.desc())
        .first()
    )
    if last_rating:
        if datetime.utcnow() - last_rating.created_at < timedelta(minutes=5):
            raise HTTPException(status_code=429, detail="COOLDOWN_RATING_5MIN")

    rating = crud.create_rating(db, item_id, user.id, payload.a, payload.b, payload.c, payload.d, payload.n)
    return rating


@app.get("/stats/ranking", response_model=list[schemas.RankingEntry])
def ranking(range: str = "all", db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if range not in {"7", "30", "all"}:
        raise HTTPException(status_code=400, detail="Invalid range")
    return stats.get_ranking(db, range)


@app.get("/items/summary", response_model=list[schemas.ItemSummaryOut])
def items_summary(range: str = "all", db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if range not in {"7", "30", "all"}:
        raise HTTPException(status_code=400, detail="Invalid range")
    return stats.get_items_summary(db, range, user)


@app.get("/items/{item_id}/stats", response_model=schemas.ItemStatsOut)
def item_stats(item_id: str, range: str = "all", db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if range not in {"7", "30", "all"}:
        raise HTTPException(status_code=400, detail="Invalid range")
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return stats.get_item_stats(db, item_id, range)


@app.get("/items/{item_id}/ratings/summary", response_model=schemas.RatingsSummaryOut)
def ratings_summary(item_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return stats.get_ratings_summary(db, item_id, user)


@app.get("/items/{item_id}/others", response_model=schemas.RatingsSummaryOut)
def ratings_others(item_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return stats.get_ratings_summary(db, item_id, user)


@app.get("/items/{item_id}/detail", response_model=schemas.ItemDetailOut)
def item_detail(item_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return stats.get_item_detail(db, item_id, user)


@app.get("/rankings", response_model=schemas.RankingsOut)
def rankings(mode: str = "global", db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if mode not in {"mine", "global"}:
        raise HTTPException(status_code=400, detail="Invalid mode")
    return stats.get_rankings(db, user, mode)
