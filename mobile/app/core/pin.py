from __future__ import annotations

import json
import os
import time
from typing import Optional


class PinStore:
    _PINS = {
        1: "3221",
        2: "6969",
        3: "2626",
        4: "3859",
    }

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._cooldown_path = os.path.join(base_dir, "name_view_cooldowns.json")

    def verify_pin(self, profile_num: int, pin: str) -> bool:
        return str(pin).strip() == self._PINS.get(profile_num)

    def _load_cooldowns(self) -> dict:
        if not os.path.exists(self._cooldown_path):
            return {}
        with open(self._cooldown_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}

    def _save_cooldowns(self, data: dict) -> None:
        with open(self._cooldown_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def can_view_name(self, profile_num: int, item_id: str) -> tuple[bool, int]:
        data = self._load_cooldowns()
        profile_data = data.get(str(profile_num), {})
        until = float(profile_data.get(item_id, 0))
        now = time.time()
        remaining = max(0, int(until - now))
        return remaining == 0, remaining

    def mark_viewed_name(self, profile_num: int, item_id: str) -> None:
        data = self._load_cooldowns()
        key = str(profile_num)
        profile_data = data.get(key, {})
        profile_data[item_id] = time.time() + 300
        data[key] = profile_data
        self._save_cooldowns(data)

    @staticmethod
    def format_mmss(seconds: int) -> str:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
