from __future__ import annotations

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from .base import BaseScreen
from app.core.session import SessionStore


PROFILE_CREDENTIALS = {
    1: ("p1", "p1pass"),
    2: ("p2", "p2pass"),
    3: ("p3", "p3pass"),
    4: ("p4", "p4pass"),
}


class ProfileSelectScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pin_dialog: MDDialog | None = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="24dp", spacing="12dp")

        title = MDLabel(text="Perfil", halign="center", font_style="H4", size_hint_y=None)
        title.bind(texture_size=lambda *_: setattr(title, "height", title.texture_size[1]))
        root.add_widget(title)

        for key in [1, 2, 3, 4]:
            btn = MDRaisedButton(text=str(key), on_release=lambda _, k=key: self.on_select(k))
            root.add_widget(btn)

        self.add_widget(root)

    def on_select(self, profile_num: int):
        SessionStore.set_profile(profile_num)
        app = self.manager.app if self.manager else None
        if not app:
            return
        self._prompt_verify_pin(profile_num)

    def _prompt_verify_pin(self, profile_num: int):
        pin = MDTextField(password=True, hint_text="PIN", input_filter="int")

        content = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None)
        content.height = 80
        content.add_widget(pin)

        def _verify(_instance):
            p = pin.text.strip()
            app = self.manager.app
            if not app.pin_store.verify_pin(profile_num, p):
                self.show_error("PIN incorrecto")
                return
            self._dismiss_pin_dialog()
            self._login_profile(profile_num)

        self._pin_dialog = MDDialog(
            title="PIN requerido",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda *_: self._dismiss_pin_dialog()),
                MDFlatButton(text="OK", on_release=_verify),
            ],
        )
        self._pin_dialog.open()

    def _dismiss_pin_dialog(self):
        if self._pin_dialog:
            self._pin_dialog.dismiss()
            self._pin_dialog = None

    def _login_profile(self, profile_num: int):
        app = self.manager.app if self.manager else None
        if not app:
            return
        username, password = PROFILE_CREDENTIALS[profile_num]
        existing = SessionStore.get_token(profile_num)
        if existing:
            app.api.set_token(existing)
            self.manager.current = "items"
            return

        def _do():
            return app.api.login(username, password)

        def _ok(token: str):
            SessionStore.set_token(profile_num, token)
            app.api.set_token(token)
            self.show_info("Acceso OK")
            self.manager.current = "items"

        def _err(message: str):
            if "No se puede conectar" in message:
                self.show_error("Servidor no disponible")
            else:
                self.show_error(message)

        self.run_bg(_do, on_success=_ok, on_error=_err)
