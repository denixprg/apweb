from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    invite_code: str
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    is_admin: bool
    is_blocked: bool
    created_at: datetime

    class Config:
        orm_mode = True


class MeOut(BaseModel):
    id: str
    username: str
    is_admin: bool

    class Config:
        orm_mode = True


class InviteCreate(BaseModel):
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class InviteOut(BaseModel):
    code: str
    expires_at: Optional[datetime]


class ItemCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=0, max_length=200)


class ItemUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=32)
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)


class ItemOut(BaseModel):
    id: str
    code: str
    name: str
    created_at: datetime

    class Config:
        orm_mode = True


class RatingCreate(BaseModel):
    a: int = Field(ge=0, le=10)
    b: int = Field(ge=0, le=10)
    c: int = Field(ge=0, le=10)
    d: int = Field(ge=0, le=10)
    n: int = Field(ge=0, le=2)


class RatingOut(BaseModel):
    id: str
    item_id: str
    user_id: str
    a: int
    b: int
    c: int
    d: int
    n: int
    created_at: datetime

    class Config:
        orm_mode = True


class RankingEntry(BaseModel):
    item_id: str
    code: str
    name: str
    avg_total: float
    count: int


class ItemStatsOut(BaseModel):
    item_id: str
    code: str
    name: str
    avg_a: float
    avg_b: float
    avg_c: float
    avg_d: float
    avg_n: float
    avg_total: float
    ratings: List[RatingOut]


class ItemSummaryOut(BaseModel):
    id: str
    code: str
    name: Optional[str]
    my_best_total: Optional[float]
    my_best_a: Optional[float]
    my_best_b: Optional[float]
    my_best_c: Optional[float]
    my_best_d: Optional[float]
    my_best_n: Optional[float]
    my_avg_total: Optional[float]
    my_avg_a: Optional[float]
    my_avg_b: Optional[float]
    my_avg_c: Optional[float]
    my_avg_d: Optional[float]
    my_avg_n: Optional[float]
    global_best_total: Optional[float]
    global_avg_total: Optional[float]


class RatingsSummaryOut(BaseModel):
    item_id: str
    others_count: int
    others_avg: dict
    others_best: dict
    others_last: List[dict]


class RatingInline(BaseModel):
    a: int
    b: int
    c: int
    d: int
    n: int
    total: int
    created_at: datetime


class ProfileRating(BaseModel):
    profile: str
    rating: Optional[RatingInline]


class ItemDetailOut(BaseModel):
    item: dict
    my_rating: Optional[RatingInline]
    ratings_by_profile: List[ProfileRating]
    can_view_others: bool


class RankingEntryOut(BaseModel):
    item_id: str
    code: str
    value: float


class RankingsOut(BaseModel):
    total: List[RankingEntryOut]
    a: List[RankingEntryOut]
    b: List[RankingEntryOut]
    c: List[RankingEntryOut]
    d: List[RankingEntryOut]
    n: List[RankingEntryOut]
