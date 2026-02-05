from __future__ import annotations

import os
import requests
from typing import Any, Dict, Optional

DEFAULT_API_URL = os.getenv("API_URL", "https://apweb-zhfm.onrender.com")


class ApiClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or DEFAULT_API_URL).rstrip("/")
        self.token: Optional[str] = None

    def set_token(self, token: Optional[str]) -> None:
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            return requests.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                timeout=10,
                **kwargs,
            )
        except requests.Timeout as exc:
            raise RuntimeError("No se puede conectar al servidor") from exc
        except requests.RequestException as exc:
            raise RuntimeError("No se puede conectar al servidor") from exc

    def _handle(self, resp: requests.Response) -> Dict[str, Any]:
        try:
            data = resp.json()
        except Exception:
            data = {"detail": "Invalid response"}
        if resp.status_code >= 400:
            if resp.status_code == 401:
                raise RuntimeError("SESSION_EXPIRED")
            if resp.status_code == 403:
                raise RuntimeError("ACCOUNT_BLOCKED")
            detail = data.get("detail") if isinstance(data, dict) else "Error"
            raise RuntimeError(str(detail))
        return data

    def login(self, username: str, password: str) -> str:
        resp = self._request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
        )

        try:
            data = resp.json()
        except Exception:
            data = {}

        if resp.status_code in (401, 403):
            detail = ""
            if isinstance(data, dict):
                detail = str(data.get("detail", ""))
            if resp.status_code == 403 or "blocked" in detail.lower():
                raise RuntimeError("Cuenta bloqueada")
            raise RuntimeError("Usuario o contraseña incorrectos")

        if resp.status_code >= 400:
            detail = data.get("detail") if isinstance(data, dict) else "Error"
            raise RuntimeError(str(detail))

        token = None
        if isinstance(data, dict):
            token = data.get("access_token") or data.get("token")
        if not token:
            raise RuntimeError("Respuesta inválida del backend (token faltante)")
        return token

    def register(self, invite_code: str, username: str, password: str) -> Dict[str, Any]:
        resp = self._request(
            "POST",
            "/auth/register",
            json={"invite_code": invite_code, "username": username, "password": password},
        )
        return self._handle(resp)

    def get_items(self) -> Dict[str, Any]:
        resp = self._request("GET", "/items")
        return self._handle(resp)

    def create_item(self, code: str, name: Optional[str] = None) -> Dict[str, Any]:
        payload = {"code": code, "name": "" if name is None else name}
        resp = self._request("POST", "/items", json=payload)
        return self._handle(resp)

    def create_rating(self, item_id: str, a: int, b: int, c: int, d: int, n: int) -> Dict[str, Any]:
        resp = self._request(
            "POST",
            f"/items/{item_id}/ratings",
            json={"a": a, "b": b, "c": c, "d": d, "n": n},
        )
        return self._handle(resp)

    def get_ranking(self, range_key: str = "all") -> Dict[str, Any]:
        resp = self._request("GET", "/stats/ranking", params={"range": range_key})
        return self._handle(resp)

    def get_item_stats(self, item_id: str, range_key: str = "all") -> Dict[str, Any]:
        resp = self._request("GET", f"/items/{item_id}/stats", params={"range": range_key})
        return self._handle(resp)

    def get_items_summary(self, range_key: str = "all") -> Dict[str, Any]:
        resp = self._request("GET", "/items/summary", params={"range": range_key})
        return self._handle(resp)

    def delete_item(self, item_id: str) -> Dict[str, Any]:
        resp = self._request("DELETE", f"/items/{item_id}")
        if resp.status_code in (404, 405):
            raise RuntimeError("NOT_IMPLEMENTED")
        return self._handle(resp)

    def get_item_ratings_summary(self, item_id: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/items/{item_id}/ratings/summary")
        return self._handle(resp)

    def get_others(self, item_id: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/items/{item_id}/others")
        return self._handle(resp)

    def get_item_detail(self, item_id: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/items/{item_id}/detail")
        return self._handle(resp)

    def get_rankings(self, mode: str = "global") -> Dict[str, Any]:
        try:
            resp = self._request("GET", "/rankings", params={"mode": mode})
        except RuntimeError as exc:
            raise

        if resp.status_code == 404:
            raise RuntimeError("RANKINGS_404")
        if resp.status_code == 401:
            raise RuntimeError("SESSION_EXPIRED")
        if resp.status_code == 403:
            try:
                data = resp.json()
            except Exception:
                data = {}
            detail = data.get("detail", "Forbidden")
            raise RuntimeError(f"FORBIDDEN:{detail}")
        return self._handle(resp)

    def list_items(self) -> Dict[str, Any]:
        return self.get_items()

    def rate_item(self, item_id: str, a: int, b: int, c: int, d: int, n: int) -> Dict[str, Any]:
        return self.create_rating(item_id, a, b, c, d, n)
