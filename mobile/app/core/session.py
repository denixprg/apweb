from __future__ import annotations

from typing import Optional


class SessionStore:
    _token: Optional[str] = None
    _profile: Optional[int] = None
    _tokens_by_profile: dict[int, Optional[str]] = {}

    @classmethod
    def set_profile(cls, profile_num: int) -> None:
        cls._profile = profile_num
        cls._token = cls._tokens_by_profile.get(profile_num)

    @classmethod
    def get_profile(cls) -> Optional[int]:
        return cls._profile

    @classmethod
    def set_token(cls, profile_num: int, token: Optional[str]) -> None:
        cls._tokens_by_profile[profile_num] = token
        if cls._profile == profile_num:
            cls._token = token

    @classmethod
    def get_token(cls, profile_num: int) -> Optional[str]:
        return cls._tokens_by_profile.get(profile_num)

    @classmethod
    def clear_token(cls, profile_num: int) -> None:
        cls._tokens_by_profile.pop(profile_num, None)
        if cls._profile == profile_num:
            cls._token = None

    @classmethod
    def set_current_token(cls, token: Optional[str]) -> None:
        cls._token = token

    @classmethod
    def clear_current_token(cls) -> None:
        cls._token = None

    @classmethod
    def is_logged_in(cls) -> bool:
        return bool(cls._token)

    @classmethod
    def get_current_token(cls) -> Optional[str]:
        return cls._token
