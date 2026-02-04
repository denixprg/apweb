from __future__ import annotations

from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog

from .base import BaseScreen


class ItemDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.item_id: str | None = None
        self.item_code: str | None = None
        self._data = {}

        self.topbar: MDTopAppBar | None = None
        self.list_box: MDBoxLayout | None = None
        self.lock_label: MDLabel | None = None

        self.slider_a: MDSlider | None = None
        self.slider_b: MDSlider | None = None
        self.slider_c: MDSlider | None = None
        self.slider_d: MDSlider | None = None
        self.val_a: MDLabel | None = None
        self.val_b: MDLabel | None = None
        self.val_c: MDLabel | None = None
        self.val_d: MDLabel | None = None
        self.n0_btn: MDRaisedButton | None = None
        self.n1_btn: MDRaisedButton | None = None
        self.n2_btn: MDRaisedButton | None = None
        self.selected_n = 0
        self.save_btn: MDRaisedButton | None = None
        self.action_btn: MDRaisedButton | None = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        self.topbar = MDTopAppBar(
            title="Detalle",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
        )
        root.add_widget(self.topbar)

        scroll = ScrollView()
        content = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        root.add_widget(scroll)

        title = MDLabel(text="Puntuaciones (1-4)", font_style="H6", size_hint_y=None)
        title.bind(texture_size=lambda *_: setattr(title, "height", title.texture_size[1]))
        content.add_widget(title)

        self.list_box = MDBoxLayout(orientation="vertical", spacing="6dp", size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        content.add_widget(self.list_box)

        self.lock_label = MDLabel(
            text="Puntúa para ver a los demás",
            halign="center",
            size_hint_y=None,
        )
        self.lock_label.bind(texture_size=lambda *_: setattr(self.lock_label, "height", self.lock_label.texture_size[1]))
        content.add_widget(self.lock_label)

        self.action_btn = MDRaisedButton(text="Puntuar ahora", pos_hint={"center_x": 0.5})
        self.action_btn.bind(on_release=lambda *_: self.open_score())
        content.add_widget(self.action_btn)

        self.add_widget(root)

    def _add_slider_row(self, root: MDBoxLayout, label: str) -> MDLabel:
        row = MDBoxLayout(size_hint_y=None)
        row.height = 28
        row.add_widget(MDLabel(text=label))
        value_label = MDLabel(text="0", halign="right")
        row.add_widget(value_label)
        root.add_widget(row)
        return value_label

    def _add_slider(self, root: MDBoxLayout, key: str) -> MDSlider:
        slider = MDSlider(min=0, max=10, value=0, step=1)
        slider.bind(value=lambda _s, v: self.update_value(key, v))
        root.add_widget(slider)
        return slider

    def set_item(self, item_id: str, item_code: str | None = None):
        self.item_id = item_id
        if item_code:
            self.item_code = item_code
        self.refresh()

    def refresh(self):
        if not self.item_id:
            return

        def _do():
            return self.manager.app.api.get_item_detail(self.item_id)

        def _ok(data):
            self._data = data or {}
            item = self._data.get("item") or {}
            self.item_code = item.get("code")
            if self.topbar and self.item_code:
                self.topbar.title = f"{self.item_code}"
            self._render_profiles()
            self._update_action_label()

        def _err(message: str):
            if self.handle_session_error(message):
                return
            self.show_error("Servidor no disponible" if "No se puede conectar" in message else message)

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def _render_profiles(self):
        if not self.list_box or not self.lock_label:
            return
        self.list_box.clear_widgets()
        can_view = bool(self._data.get("can_view_others"))
        self.lock_label.opacity = 0 if can_view else 1
        self.lock_label.height = self.lock_label.texture_size[1] if not can_view else 0

        ratings = self._data.get("ratings_by_profile") or []
        for entry in ratings:
            profile = entry.get("profile", "?")
            rating = entry.get("rating")
            if not can_view:
                text = f"P{profile}  | —"
            elif not rating:
                text = f"P{profile}  | —"
            else:
                text = (
                    f"P{profile}  | Total {rating.get('total')} | "
                    f"A {rating.get('a')} B {rating.get('b')} C {rating.get('c')} "
                    f"D {rating.get('d')} N {rating.get('n')}"
                )
            lbl = MDLabel(text=text, size_hint_y=None)
            lbl.bind(texture_size=lambda *_: setattr(lbl, "height", lbl.texture_size[1]))
            self.list_box.add_widget(lbl)

    def _update_action_label(self):
        if not self.action_btn:
            return
        my_rating = self._data.get("my_rating")
        if my_rating:
            self.action_btn.text = "Modificar mi puntuación"
        else:
            self.action_btn.text = "Puntuar ahora"

    def open_score(self):
        if not self.item_id:
            return
        my_rating = self._data.get("my_rating")
        screen = self.manager.get_screen("score")
        screen.set_item(self.item_id, self.item_code or "", prefill_rating=my_rating)
        self.manager.current = "score"

    def go_back(self):
        self.manager.current = "items"
