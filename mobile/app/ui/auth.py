from __future__ import annotations

from kivy.lang import Builder
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

from .base import BaseScreen
from app.core.session import SessionStore

KV = """
<AuthScreen>:
    name: "auth"
    MDBoxLayout:
        orientation: "vertical"
        padding: "24dp"
        spacing: "12dp"

        MDLabel:
            text: "Acceso"
            halign: "center"
            font_style: "H4"
            size_hint_y: None
            height: self.texture_size[1]

        MDTextField:
            id: username
            hint_text: "Usuario"
            helper_text: "Requerido"
            helper_text_mode: "on_focus"

        MDTextField:
            id: password
            hint_text: "Password"
            password: True
            helper_text: "Requerido"
            helper_text_mode: "on_focus"

        MDRaisedButton:
            text: "Login"
            pos_hint: {"center_x": 0.5}
            on_release: root.on_login()

        MDSeparator:
            height: "1dp"

        MDLabel:
            text: "Registro"
            halign: "center"
            font_style: "H5"
            size_hint_y: None
            height: self.texture_size[1]

        MDTextField:
            id: invite
            hint_text: "Invite code"

        MDTextField:
            id: reg_username
            hint_text: "Usuario"

        MDTextField:
            id: reg_password
            hint_text: "Password"
            password: True

        MDRaisedButton:
            text: "Registrarme"
            pos_hint: {"center_x": 0.5}
            on_release: root.on_register()
"""


class AuthScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(KV)

    def on_login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()
        if not username or not password:
            self.show_error("Completa usuario y password")
            return

        def _do():
            return self.manager.app.api.login(username, password)

        def _ok(data):
            token = data.get("access_token")
            if not token:
                self.show_error("Token inválido")
                return
            self.manager.app.api.set_token(token)
            self.manager.current = "items"

        self.run_bg(_do, on_success=_ok, on_error=self.show_error)

    def on_register(self):
        invite = self.ids.invite.text.strip()
        username = self.ids.reg_username.text.strip()
        password = self.ids.reg_password.text.strip()
        if not invite or not username or not password:
            self.show_error("Completa invite, usuario y password")
            return

        def _do():
            return self.manager.app.api.register(invite, username, password)

        def _ok(_data):
            self.show_info("Registro OK, ahora haz login")

        self.run_bg(_do, on_success=_ok, on_error=self.show_error)


class LoginScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(KV)
        self._build_ui()

    def _build_ui(self):
        layout = MDBoxLayout(
            orientation="vertical",
            padding="32dp",
            spacing="16dp",
        )

        title = MDLabel(
            text="Rating App",
            halign="center",
            font_style="H3",
            size_hint_y=None,
        )
        title.bind(texture_size=lambda *_: setattr(title, "height", title.texture_size[1]))

        self.username_field = MDTextField(
            hint_text="Usuario",
            helper_text="Requerido",
            helper_text_mode="on_focus",
        )
        self.password_field = MDTextField(
            hint_text="Contraseña",
            password=True,
            helper_text="Requerido",
            helper_text_mode="on_focus",
        )

        self.login_button = MDRaisedButton(
            text="Login",
            pos_hint={"center_x": 0.5},
            on_release=lambda *_: self.on_login(),
        )

        layout.add_widget(title)
        layout.add_widget(self.username_field)
        layout.add_widget(self.password_field)
        layout.add_widget(self.login_button)
        self.add_widget(layout)

    def on_login(self):
        username = self.username_field.text.strip()
        password = self.password_field.text.strip()
        if not username or not password:
            self.show_error("Completa usuario y contraseña")
            return
        self.login_button.disabled = True

        def _do():
            return self.manager.app.api.login(username, password)

        def _ok(token: str):
            SessionStore.set_current_token(token)
            self.manager.app.api.set_token(token)
            self.show_info("Login OK")
            self.manager.current = "items"
            self.login_button.disabled = False

        def _err(message: str):
            self.show_error(message)
            self.login_button.disabled = False

        self.run_bg(_do, on_success=_ok, on_error=_err)
