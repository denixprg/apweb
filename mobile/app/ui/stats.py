from __future__ import annotations

from typing import List, Dict, Any

from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, TwoLineListItem, OneLineListItem
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.app import MDApp

from .base import BaseScreen


class StatsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.range_key = "all"
        self.items_list: MDList | None = None
        self.loading_label: MDLabel | None = None
        self.btn_7: MDRaisedButton | None = None
        self.btn_30: MDRaisedButton | None = None
        self.btn_all: MDRaisedButton | None = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        topbar = MDTopAppBar(
            title="Stats",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
        )
        root.add_widget(topbar)

        range_box = MDBoxLayout(spacing="8dp", size_hint_y=None)
        range_box.height = 48
        self.btn_7 = MDRaisedButton(text="7 días", on_release=lambda *_: self.set_range("7"))
        self.btn_30 = MDRaisedButton(text="30 días", on_release=lambda *_: self.set_range("30"))
        self.btn_all = MDRaisedButton(text="Todo", on_release=lambda *_: self.set_range("all"))
        range_box.add_widget(self.btn_7)
        range_box.add_widget(self.btn_30)
        range_box.add_widget(self.btn_all)
        root.add_widget(range_box)

        scroll = ScrollView()
        self.items_list = MDList()
        scroll.add_widget(self.items_list)
        root.add_widget(scroll)

        self.loading_label = MDLabel(
            text="Cargando...",
            halign="center",
            size_hint_y=None,
        )
        self.loading_label.bind(texture_size=lambda *_: setattr(self.loading_label, "height", self.loading_label.texture_size[1]))
        self.loading_label.opacity = 0
        root.add_widget(self.loading_label)

        self.add_widget(root)
        self._set_range_styles()

    def on_pre_enter(self, *args):
        self.refresh()

    def go_back(self):
        self.manager.current = "items"

    def set_range(self, key: str):
        self.range_key = key
        self._set_range_styles()
        self.refresh()

    def _set_range_styles(self):
        app = MDApp.get_running_app()
        theme = app.theme_cls if app else None
        buttons = {
            "7": self.btn_7,
            "30": self.btn_30,
            "all": self.btn_all,
        }
        for key, btn in buttons.items():
            if not btn or not theme:
                continue
            if key == self.range_key:
                btn.md_bg_color = theme.primary_color
            else:
                btn.md_bg_color = theme.disabled_hint_text_color

    def refresh(self):
        if self.loading_label:
            self.loading_label.opacity = 1
            self.loading_label.height = self.loading_label.texture_size[1]

        def _do():
            return self.manager.app.api.get_ranking(self.range_key)

        def _ok(data):
            self._render_list(data or [])
            if self.loading_label:
                self.loading_label.opacity = 0
                self.loading_label.height = 0

        def _err(message: str):
            if self.handle_session_error(message):
                return
            self.show_error("No se pudo cargar (offline)")
            if self.loading_label:
                self.loading_label.opacity = 0
                self.loading_label.height = 0

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def _render_list(self, items: List[Dict[str, Any]]):
        if not self.items_list:
            self.show_error("UI incompleta: lista no disponible")
            return
        self.items_list.clear_widgets()
        if not items:
            self.items_list.add_widget(OneLineListItem(text="Sin datos"))
            return
        for item in items:
            code = item.get("code")
            item_id = item.get("item_id")
            total = item.get("avg_total")
            total_text = f"Total: {total:.2f}" if isinstance(total, (int, float)) else "Total: -"
            li = TwoLineListItem(
                text=str(code),
                secondary_text=total_text,
                on_release=lambda x, iid=item_id, icode=code: self.open_item_stats(iid, icode),
            )
            self.items_list.add_widget(li)

    def open_item_stats(self, item_id: str, item_code: str):
        screen = self.manager.get_screen("item_stats")
        screen.set_item(item_id, item_code, self.range_key)
        self.manager.current = "item_stats"


class ItemStatsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.item_id: str | None = None
        self.item_code: str | None = None
        self.range_key = "all"

        self.header_label: MDLabel | None = None
        self.stats_box: MDBoxLayout | None = None
        self.ratings_list: MDList | None = None
        self.loading_label: MDLabel | None = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        topbar = MDTopAppBar(
            title="Detalle",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
        )
        root.add_widget(topbar)

        self.header_label = MDLabel(
            text="Item",
            halign="center",
            font_style="H5",
            size_hint_y=None,
        )
        self.header_label.bind(texture_size=lambda *_: setattr(self.header_label, "height", self.header_label.texture_size[1]))
        root.add_widget(self.header_label)

        self.stats_box = MDBoxLayout(orientation="vertical", spacing="4dp", size_hint_y=None)
        self.stats_box.height = 140
        root.add_widget(self.stats_box)

        ratings_label = MDLabel(text="Últimas 10 puntuaciones", size_hint_y=None)
        ratings_label.bind(texture_size=lambda *_: setattr(ratings_label, "height", ratings_label.texture_size[1]))
        root.add_widget(ratings_label)

        scroll = ScrollView()
        self.ratings_list = MDList()
        scroll.add_widget(self.ratings_list)
        root.add_widget(scroll)

        self.loading_label = MDLabel(
            text="Cargando...",
            halign="center",
            size_hint_y=None,
        )
        self.loading_label.bind(texture_size=lambda *_: setattr(self.loading_label, "height", self.loading_label.texture_size[1]))
        self.loading_label.opacity = 0
        root.add_widget(self.loading_label)

        self.add_widget(root)

    def set_item(self, item_id: str, item_code: str, range_key: str):
        self.item_id = item_id
        self.item_code = item_code
        self.range_key = range_key
        if self.header_label:
            self.header_label.text = f"Item: {item_code}"
        self.refresh()

    def go_back(self):
        self.manager.current = "stats"

    def refresh(self):
        if self.loading_label:
            self.loading_label.opacity = 1
            self.loading_label.height = self.loading_label.texture_size[1]

        def _do():
            return self.manager.app.api.get_item_stats(self.item_id, self.range_key)

        def _ok(data):
            self._render_stats(data or {})
            if self.loading_label:
                self.loading_label.opacity = 0
                self.loading_label.height = 0

        def _err(message: str):
            if self.handle_session_error(message):
                return
            self.show_error("No se pudo cargar (offline)")
            if self.loading_label:
                self.loading_label.opacity = 0
                self.loading_label.height = 0

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def _render_stats(self, data: Dict[str, Any]):
        if not self.stats_box or not self.ratings_list:
            self.show_error("UI incompleta: stats no disponibles")
            return

        self.stats_box.clear_widgets()
        def _add_stat(label: str, value: Any):
            text = f"{label}: {value:.2f}" if isinstance(value, (int, float)) else f"{label}: -"
            self.stats_box.add_widget(MDLabel(text=text, size_hint_y=None))

        _add_stat("A", data.get("avg_a"))
        _add_stat("B", data.get("avg_b"))
        _add_stat("C", data.get("avg_c"))
        _add_stat("D", data.get("avg_d"))
        _add_stat("N", data.get("avg_n"))
        _add_stat("Total", data.get("avg_total"))

        self.ratings_list.clear_widgets()
        ratings = data.get("ratings") or []
        last_ratings = ratings[-10:]
        if not last_ratings:
            self.ratings_list.add_widget(OneLineListItem(text="Sin puntuaciones"))
            return
        for r in last_ratings:
            text = f"A:{r.get('a')} B:{r.get('b')} C:{r.get('c')} D:{r.get('d')} N:{r.get('n')}"
            self.ratings_list.add_widget(OneLineListItem(text=text))
