from __future__ import annotations

from sqlalchemy.orm import Session

from . import crud, models
BOOTSTRAP_USERS = [
    ("p1", "p1pass", False),
    ("p2", "p2pass", False),
    ("p3", "p3pass", True),
    ("p4", "p4pass", False),
]


def ensure_bootstrap_users(db: Session) -> None:
    for username, password, is_admin in BOOTSTRAP_USERS:
        user = crud.get_user_by_username(db, username)
        if user:
            if is_admin and not user.is_admin:
                user.is_admin = True
                user.is_blocked = False
                db.add(user)
                db.commit()
            continue
        crud.create_user(db, username, password, is_admin=is_admin)
    print("BOOTSTRAP: perfiles listos (p1,p2,p3,p4)")
