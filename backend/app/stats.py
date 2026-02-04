from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from . import models, schemas


def _range_start(range_name: str):
    if range_name == "7":
        return datetime.utcnow() - timedelta(days=7)
    if range_name == "30":
        return datetime.utcnow() - timedelta(days=30)
    return None


def get_ranking(db: Session, range_name: str) -> List[schemas.RankingEntry]:
    start = _range_start(range_name)
    query = db.query(
        models.Item.id.label("item_id"),
        models.Item.code.label("code"),
        models.Item.name.label("name"),
        func.avg((models.Rating.a + models.Rating.b + models.Rating.c + models.Rating.d) / 4.0 + models.Rating.n).label("avg_total"),
        func.count(models.Rating.id).label("count"),
    ).join(models.Rating, models.Rating.item_id == models.Item.id)

    if start:
        query = query.filter(models.Rating.created_at >= start)

    rows = query.group_by(models.Item.id).order_by(func.avg((models.Rating.a + models.Rating.b + models.Rating.c + models.Rating.d) / 4.0 + models.Rating.n).desc()).all()

    return [
        schemas.RankingEntry(
            item_id=str(r.item_id),
            code=r.code,
            name=r.name,
            avg_total=float(r.avg_total or 0),
            count=int(r.count or 0),
        )
        for r in rows
    ]


def get_item_stats(db: Session, item_id: str, range_name: str) -> schemas.ItemStatsOut:
    start = _range_start(range_name)
    base_query = db.query(models.Rating).filter(models.Rating.item_id == item_id)
    if start:
        base_query = base_query.filter(models.Rating.created_at >= start)

    agg = db.query(
        func.avg(models.Rating.a),
        func.avg(models.Rating.b),
        func.avg(models.Rating.c),
        func.avg(models.Rating.d),
        func.avg(models.Rating.n),
        func.avg((models.Rating.a + models.Rating.b + models.Rating.c + models.Rating.d) / 4.0 + models.Rating.n),
    ).filter(models.Rating.item_id == item_id)

    if start:
        agg = agg.filter(models.Rating.created_at >= start)

    avg_a, avg_b, avg_c, avg_d, avg_n, avg_total = agg.first()

    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    ratings = base_query.order_by(models.Rating.created_at.desc()).limit(10).all()

    return schemas.ItemStatsOut(
        item_id=str(item.id),
        code=item.code,
        name=item.name,
        avg_a=float(avg_a or 0),
        avg_b=float(avg_b or 0),
        avg_c=float(avg_c or 0),
        avg_d=float(avg_d or 0),
        avg_n=float(avg_n or 0),
        avg_total=float(avg_total or 0),
        ratings=ratings,
    )


def get_items_summary(db: Session, range_name: str, user: models.User) -> List[schemas.ItemSummaryOut]:
    start = _range_start(range_name)
    if start:
        join_cond = and_(models.Rating.item_id == models.Item.id, models.Rating.created_at >= start)
    else:
        join_cond = models.Rating.item_id == models.Item.id

    total_expr = (models.Rating.a + models.Rating.b + models.Rating.c + models.Rating.d + models.Rating.n)

    user_join = and_(join_cond, models.Rating.user_id == user.id)

    def _my_max(expr):
        return func.max(case((user_join, expr), else_=None))

    rows = (
        db.query(
            models.Item.id.label("item_id"),
            models.Item.code.label("code"),
            models.Item.name.label("name"),
            _my_max(total_expr).label("my_best_total"),
            _my_max(models.Rating.a).label("my_best_a"),
            _my_max(models.Rating.b).label("my_best_b"),
            _my_max(models.Rating.c).label("my_best_c"),
            _my_max(models.Rating.d).label("my_best_d"),
            _my_max(models.Rating.n).label("my_best_n"),
            func.avg(case((user_join, total_expr), else_=None)).label("my_avg_total"),
            func.avg(case((user_join, models.Rating.a), else_=None)).label("my_avg_a"),
            func.avg(case((user_join, models.Rating.b), else_=None)).label("my_avg_b"),
            func.avg(case((user_join, models.Rating.c), else_=None)).label("my_avg_c"),
            func.avg(case((user_join, models.Rating.d), else_=None)).label("my_avg_d"),
            func.avg(case((user_join, models.Rating.n), else_=None)).label("my_avg_n"),
            func.max(total_expr).label("global_best_total"),
            func.avg(total_expr).label("global_avg_total"),
        )
        .outerjoin(models.Rating, join_cond)
        .group_by(models.Item.id)
        .order_by(models.Item.code.asc())
        .all()
    )

    def _f(value):
        return float(value) if value is not None else None

    results = []
    for r in rows:
        data = {
            "id": str(r.item_id),
            "code": r.code,
            "name": r.name,
            "my_best_total": _f(r.my_best_total),
            "my_best_a": _f(r.my_best_a),
            "my_best_b": _f(r.my_best_b),
            "my_best_c": _f(r.my_best_c),
            "my_best_d": _f(r.my_best_d),
            "my_best_n": _f(r.my_best_n),
            "my_avg_total": _f(r.my_avg_total),
            "my_avg_a": _f(r.my_avg_a),
            "my_avg_b": _f(r.my_avg_b),
            "my_avg_c": _f(r.my_avg_c),
            "my_avg_d": _f(r.my_avg_d),
            "my_avg_n": _f(r.my_avg_n),
            "global_best_total": _f(r.global_best_total) if user.is_admin else None,
            "global_avg_total": _f(r.global_avg_total) if user.is_admin else None,
        }
        results.append(schemas.ItemSummaryOut(**data))
    return results


def _profile_alias(username: str) -> str:
    mapping = {"p1": "1", "p2": "2", "p3": "3", "p4": "4"}
    return mapping.get(username, "u")


def get_ratings_summary(db: Session, item_id: str, user: models.User) -> schemas.RatingsSummaryOut:
    has_own = (
        db.query(models.Rating.id)
        .filter(models.Rating.item_id == item_id, models.Rating.user_id == user.id)
        .first()
    )
    if not has_own:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="RATE_FIRST_TO_VIEW_OTHERS")

    others_query = (
        db.query(models.Rating)
        .filter(models.Rating.item_id == item_id, models.Rating.user_id != user.id)
        .order_by(models.Rating.created_at.desc())
    )

    others = others_query.all()
    others_count = len(others)

    if others_count == 0:
        return schemas.RatingsSummaryOut(
            item_id=str(item_id),
            others_count=0,
            others_avg={},
            others_best={},
            others_last=[],
        )

    total_expr = models.Rating.a + models.Rating.b + models.Rating.c + models.Rating.d + models.Rating.n
    agg = db.query(
        func.avg(models.Rating.a),
        func.avg(models.Rating.b),
        func.avg(models.Rating.c),
        func.avg(models.Rating.d),
        func.avg(models.Rating.n),
        func.avg(total_expr),
        func.max(models.Rating.a),
        func.max(models.Rating.b),
        func.max(models.Rating.c),
        func.max(models.Rating.d),
        func.max(models.Rating.n),
        func.max(total_expr),
    ).filter(models.Rating.item_id == item_id, models.Rating.user_id != user.id)

    (avg_a, avg_b, avg_c, avg_d, avg_n, avg_total,
     best_a, best_b, best_c, best_d, best_n, best_total) = agg.first()

    others_last = []
    user_rows = db.query(models.User.id, models.User.username).all()
    user_map = {str(uid): uname for uid, uname in user_rows}
    for r in others[:10]:
        profile_alias = _profile_alias(user_map.get(str(r.user_id), ""))
        others_last.append({
            "profile": profile_alias,
            "a": r.a,
            "b": r.b,
            "c": r.c,
            "d": r.d,
            "n": r.n,
            "total": r.a + r.b + r.c + r.d + r.n,
            "created_at": r.created_at.isoformat(),
        })

    return schemas.RatingsSummaryOut(
        item_id=str(item_id),
        others_count=others_count,
        others_avg={
            "a": float(avg_a or 0),
            "b": float(avg_b or 0),
            "c": float(avg_c or 0),
            "d": float(avg_d or 0),
            "n": float(avg_n or 0),
            "total": float(avg_total or 0),
        },
        others_best={
            "a": float(best_a or 0),
            "b": float(best_b or 0),
            "c": float(best_c or 0),
            "d": float(best_d or 0),
            "n": float(best_n or 0),
            "total": float(best_total or 0),
        },
        others_last=others_last,
    )


def get_item_detail(db: Session, item_id: str, user: models.User) -> schemas.ItemDetailOut:
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item not found")

    my_rating = (
        db.query(models.Rating)
        .filter(models.Rating.item_id == item_id, models.Rating.user_id == user.id)
        .order_by(models.Rating.created_at.desc())
        .first()
    )

    can_view_others = my_rating is not None

    profiles = [("1", "p1"), ("2", "p2"), ("3", "p3"), ("4", "p4")]
    ratings_by_profile = []

    for profile_num, username in profiles:
        rating_obj = None
        if can_view_others:
            u = db.query(models.User).filter(models.User.username == username).first()
            if u:
                r = (
                    db.query(models.Rating)
                    .filter(models.Rating.item_id == item_id, models.Rating.user_id == u.id)
                    .order_by(models.Rating.created_at.desc())
                    .first()
                )
                if r:
                    rating_obj = schemas.RatingInline(
                        a=r.a,
                        b=r.b,
                        c=r.c,
                        d=r.d,
                        n=r.n,
                        total=r.a + r.b + r.c + r.d + r.n,
                        created_at=r.created_at,
                    )
        ratings_by_profile.append(schemas.ProfileRating(profile=profile_num, rating=rating_obj))

    my_rating_out = None
    if my_rating:
        my_rating_out = schemas.RatingInline(
            a=my_rating.a,
            b=my_rating.b,
            c=my_rating.c,
            d=my_rating.d,
            n=my_rating.n,
            total=my_rating.a + my_rating.b + my_rating.c + my_rating.d + my_rating.n,
            created_at=my_rating.created_at,
        )

    return schemas.ItemDetailOut(
        item={"id": str(item.id), "code": item.code, "name": item.name},
        my_rating=my_rating_out,
        ratings_by_profile=ratings_by_profile,
        can_view_others=can_view_others,
    )


def get_rankings(db: Session, user: models.User, mode: str) -> schemas.RankingsOut:
    total_expr = (models.Rating.a + models.Rating.b + models.Rating.c + models.Rating.d + models.Rating.n)
    base = db.query(models.Item.id.label("item_id"), models.Item.code.label("code"))

    def _rank_for(expr):
        query = base.join(models.Rating, models.Rating.item_id == models.Item.id)
        if mode == "mine":
            query = query.filter(models.Rating.user_id == user.id)
            value_expr = func.max(expr)
        else:
            value_expr = func.avg(expr)
        rows = (
            query
            .group_by(models.Item.id)
            .order_by(value_expr.desc())
            .with_entities(models.Item.id, models.Item.code, value_expr.label("value"))
            .limit(50)
            .all()
        )
        return [
            schemas.RankingEntryOut(item_id=str(r.item_id), code=r.code, value=float(r.value or 0))
            for r in rows
        ]

    return schemas.RankingsOut(
        total=_rank_for(total_expr),
        a=_rank_for(models.Rating.a),
        b=_rank_for(models.Rating.b),
        c=_rank_for(models.Rating.c),
        d=_rank_for(models.Rating.d),
        n=_rank_for(models.Rating.n),
    )
