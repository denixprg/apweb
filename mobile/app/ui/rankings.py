from __future__ import annotations

from typing import Dict, Any, List

from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard

from .base import BaseScreen


class RankingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metric = "total"
        self.mode = "mine"
        self.data_cache: Dict[str, Dict[str, Any]] = {"mine": {}, "global": {}}
        self.loading_label: MDLabel | None = None
        self.list_box: MDBoxLayout | None = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        topbar = MDTopAppBar(
            title="Rankings",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
        )
        root.add_widget(topbar)

        mode_box = MDBoxLayout(spacing="6dp", size_hint_y=None)
        mode_box.height = 48
        self.btn_mine = MDRaisedButton(text="Míos", on_release=lambda *_: self.set_mode("mine"))
        self.btn_global = MDRaisedButton(text="Global", on_release=lambda *_: self.set_mode("global"))
        mode_box.add_widget(self.btn_mine)
        mode_box.add_widget(self.btn_global)
        root.add_widget(mode_box)

        metric_box = MDBoxLayout(spacing="6dp", size_hint_y=None)
        metric_box.height = 48
        for label, key in [
            ("Mejor TOTAL", "total"),
            ("Mejor A", "a"),
            ("Mejor B", "b"),
            ("Mejor C", "c"),
            ("Mejor D", "d"),
            ("Mejor N", "n"),
        ]:
            btn = MDRaisedButton(text=label, on_release=lambda _, k=key: self.set_metric(k))
            metric_box.add_widget(btn)
        root.add_widget(metric_box)

        scroll = ScrollView()
        self.list_box = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

        self.loading_label = MDLabel(text="Cargando...", halign="center", size_hint_y=None)
        self.loading_label.bind(texture_size=lambda *_: setattr(self.loading_label, "height", self.loading_label.texture_size[1]))
        self.loading_label.opacity = 0
        root.add_widget(self.loading_label)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.refresh()

    def go_back(self):
        self.manager.current = "items"

    def set_metric(self, key: str):
        self.metric = key
        self.render()

    def set_mode(self, mode: str):
        self.mode = mode
        if not self.data_cache.get(mode):
            self.refresh()
        else:
            self.render()

    def refresh(self):
        if self.loading_label:
            self.loading_label.opacity = 1
            self.loading_label.height = self.loading_label.texture_size[1]

        def _do():
            return self.manager.app.api.get_rankings(self.mode)

        def _ok(data):
            self.data_cache[self.mode] = data or {}
            if self.loading_label:
                self.loading_label.opacity = 0
                self.loading_label.height = 0
            self.render()

        def _err(message: str):
            if self.handle_session_error(message):
                return
            if message == "RANKINGS_404":
                self.show_error("Rankings no implementado (404)")
            elif message.startswith("FORBIDDEN:"):
                self.show_error(message.split("FORBIDDEN:", 1)[1])
            else:
                self.show_error("Servidor no disponible")
            if self.loading_label:
                self.loading_label.opacity = 0
                self.loading_label.height = 0

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def render(self):
        if not self.list_box:
            return
        self.list_box.clear_widgets()
        items: List[Dict[str, Any]] = (self.data_cache.get(self.mode) or {}).get(self.metric) or []
        if not items:
            empty_text = "Aún no has puntuado nada" if self.mode == "mine" else "Sin datos"
            self.list_box.add_widget(MDLabel(text=empty_text, size_hint_y=None))
            return

        for idx, row in enumerate(items, start=1):
            code = row.get("code", "")
            item_id = row.get("item_id")
            value = row.get("value")
            value_text = f"{value:.2f}" if isinstance(value, (int, float)) else "-"
            card = RankingCard(
                rank=idx,
                code=str(code),
                value_text=value_text,
                on_tap=lambda _c, iid=item_id: self.open_item(iid),
            )
            self.list_box.add_widget(card)

    def open_item(self, item_id: str):
        screen = self.manager.get_screen("item_detail")
        screen.set_item(item_id)
        self.manager.current = "item_detail"


class RankingCard(MDCard):
    def __init__(self, rank: int, code: str, value_text: str, on_tap, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.padding = ("12dp", "10dp")
        self.spacing = "8dp"
        self.size_hint_y = None
        self.height = 56
        self.radius = [12, 12, 12, 12]
        self.line_width = 1
        self.line_color = (0.6, 0.6, 0.6, 1)
        self.md_bg_color = (1, 1, 1, 1)
        self._on_tap = on_tap

        self.add_widget(MDLabel(text=f"#{rank}", size_hint_x=0.2))
        self.add_widget(MDLabel(text=code, halign="left"))
        self.add_widget(MDLabel(text=value_text, halign="right", size_hint_x=0.3))

    def on_touch_up(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_up(touch)
        if self._on_tap:
            self._on_tap(self)
        return True
