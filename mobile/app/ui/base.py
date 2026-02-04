from __future__ import annotations

from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.clock import Clock
from threading import Thread

from app.core.session import SessionStore


class BaseScreen(MDScreen):
    def show_error(self, message: str) -> None:
        Snackbar(text=message).open()

    def show_info(self, message: str) -> None:
        Snackbar(text=message).open()

    def run_bg(self, fn, on_success=None, on_error=None):
        def _dispatch_success(result):
            if on_success:
                on_success(result)

        def _dispatch_error(message: str):
            if on_error:
                on_error(message)
            else:
                self.show_error(message)

        def _worker():
            try:
                result = fn()
                Clock.schedule_once(lambda *_: _dispatch_success(result), 0)
            except Exception as exc:
                msg = str(exc)
                Clock.schedule_once(lambda *_: _dispatch_error(msg), 0)

        Thread(target=_worker, daemon=True).start()

    def handle_session_error(self, message: str) -> bool:
        if message == "SESSION_EXPIRED":
            profile = SessionStore.get_profile()
            if profile is not None:
                SessionStore.clear_token(profile)
            SessionStore.clear_current_token()
            if self.manager and getattr(self.manager, "app", None):
                self.manager.app.api.set_token(None)
            self.show_error("Sesión caducada")
            if self.manager:
                self.manager.current = "profile_select"
            return True
        if message == "ACCOUNT_BLOCKED":
            self.show_error("Cuenta bloqueada")
            return True
        return False
