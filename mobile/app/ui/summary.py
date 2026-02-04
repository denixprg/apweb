from __future__ import annotations

from typing import Dict, Any, List

from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard

from .base import BaseScreen


class SummaryScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = "global"
        self.metric = "total"
        self.data_cache: Dict[str, Dict[str, Any]] = {"mine": {}, "global": {}}
        self.loading_label: MDLabel | None = None
        self.top_total_box: MDBoxLayout | None = None
        self.top_grid: GridLayout | None = None
        self.top_bottom_box: MDBoxLayout | None = None
        self.rank_list: MDBoxLayout | None = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        topbar = MDTopAppBar(
            title="Resumen",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
        )
        root.add_widget(topbar)

        mode_box = MDBoxLayout(spacing="8dp", size_hint_y=None)
        mode_box.height = 48
        self.btn_global = MDRaisedButton(text="Global", on_release=lambda *_: self.set_mode("global"))
        self.btn_mine = MDRaisedButton(text="Míos", on_release=lambda *_: self.set_mode("mine"))
        mode_box.add_widget(self.btn_global)
        mode_box.add_widget(self.btn_mine)
        root.add_widget(mode_box)

        scroll = ScrollView()
        content = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        root.add_widget(scroll)

        section_top = MDLabel(text="Top rápido", font_style="H6", size_hint_y=None)
        section_top.bind(texture_size=lambda *_: setattr(section_top, "height", section_top.texture_size[1]))
        content.add_widget(section_top)

        self.top_total_box = MDBoxLayout(orientation="vertical", size_hint_y=None)
        self.top_total_box.bind(minimum_height=self.top_total_box.setter("height"))
        content.add_widget(self.top_total_box)

        self.top_grid = GridLayout(cols=2, spacing=8, size_hint_y=None)
        self.top_grid.bind(minimum_height=self.top_grid.setter("height"))
        content.add_widget(self.top_grid)

        self.top_bottom_box = MDBoxLayout(orientation="vertical", size_hint_y=None)
        self.top_bottom_box.bind(minimum_height=self.top_bottom_box.setter("height"))
        content.add_widget(self.top_bottom_box)

        section_rank = MDLabel(text="Ranking", font_style="H6", size_hint_y=None)
        section_rank.bind(texture_size=lambda *_: setattr(section_rank, "height", section_rank.texture_size[1]))
        content.add_widget(section_rank)

        metric_box = MDBoxLayout(spacing="6dp", size_hint_y=None)
        metric_box.height = 48
        for label, key in [
            ("TOTAL", "total"),
            ("A", "a"),
            ("B", "b"),
            ("C", "c"),
            ("D", "d"),
            ("N", "n"),
        ]:
            btn = MDRaisedButton(text=label, on_release=lambda _, k=key: self.set_metric(k))
            metric_box.add_widget(btn)
        content.add_widget(metric_box)

        self.rank_list = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None)
        self.rank_list.bind(minimum_height=self.rank_list.setter("height"))
        content.add_widget(self.rank_list)

        self.loading_label = MDLabel(text="Cargando...", halign="center", size_hint_y=None)
        self.loading_label.bind(texture_size=lambda *_: setattr(self.loading_label, "height", self.loading_label.texture_size[1]))
        self.loading_label.opacity = 0
        root.add_widget(self.loading_label)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.refresh()

    def go_back(self):
        self.manager.current = "items"

    def set_mode(self, mode: str):
        self.mode = mode
        if not self.data_cache.get(mode):
            self.refresh()
        else:
            self.render()

    def set_metric(self, key: str):
        self.metric = key
        self.render()

    def refresh(self):
        if self.loading_label:
            self.loading_label.opacity = 1
            self.loading_label.height = self.loading_label.texture_size[1]

        def _do():
            return self.manager.app.api.get_rankings(self.mode)

        def _ok(data):
            self.data_cache[self.mode] = data or {}
            print("[Summary] rankings:", self.data_cache[self.mode])
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
        data = self.data_cache.get(self.mode) or {}
        if self.top_total_box and self.top_grid and self.top_bottom_box:
            self.top_total_box.clear_widgets()
            self.top_grid.clear_widgets()
            self.top_bottom_box.clear_widgets()

            def _first_for(key: str):
                first = (data.get(key) or [None])[0]
                if isinstance(first, dict):
                    return first.get("code"), first.get("item_id"), first.get("value")
                return "—", None, None

            def _make_card(label: str, key: str):
                code, item_id, value = _first_for(key)
                return TopCard(
                    title=f"Top {label}",
                    code=str(code),
                    value_text=self._format_value(value),
                    subtitle="media global" if self.mode == "global" else "mi mejor",
                    on_tap=lambda _c, iid=item_id: self.open_item(iid),
                )

            self.top_total_box.add_widget(_make_card("TOTAL", "total"))
            self.top_grid.add_widget(_make_card("A", "a"))
            self.top_grid.add_widget(_make_card("B", "b"))
            self.top_grid.add_widget(_make_card("C", "c"))
            self.top_grid.add_widget(_make_card("D", "d"))
            self.top_bottom_box.add_widget(_make_card("N", "n"))

        if self.rank_list:
            self.rank_list.clear_widgets()
            items: List[Dict[str, Any]] = data.get(self.metric) or []
            if not items:
                empty = MDLabel(text="Aún no hay datos" if self.mode == "global" else "Aún no has puntuado nada", size_hint_y=None)
                self.rank_list.add_widget(empty)
                return
            for idx, row in enumerate(items, start=1):
                code = row.get("code", "")
                item_id = row.get("item_id")
                value = row.get("value")
                value_text = self._format_value(value)
                self.rank_list.add_widget(
                    RankingCard(
                        rank=idx,
                        code=str(code),
                        value_text=value_text,
                        on_tap=lambda _c, iid=item_id: self.open_item(iid),
                    )
                )

    def _format_value(self, value: Any) -> str:
        if not isinstance(value, (int, float)):
            return "—"
        if self.mode == "global":
            return f"{value:.1f}"
        return f"{value:.0f}"

    def open_item(self, item_id: str | None):
        if not item_id:
            return
        screen = self.manager.get_screen("item_detail")
        screen.set_item(item_id)
        self.manager.current = "item_detail"


class TopCard(MDCard):
    def __init__(self, title: str, code: str, value_text: str, subtitle: str, on_tap, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = ("12dp", "10dp")
        self.spacing = "6dp"
        self.size_hint_y = None
        self.height = 120
        self.radius = [14, 14, 14, 14]
        self.line_width = 1
        self.line_color = (0.6, 0.6, 0.6, 1)
        self.md_bg_color = (1, 1, 1, 1)
        self._on_tap = on_tap

        self.add_widget(MDLabel(text=title, size_hint_y=None))
        self.add_widget(MDLabel(text=f"[b]{code}[/b]", markup=True, font_style="H6", size_hint_y=None))
        self.add_widget(MDLabel(text=value_text, font_style="H4", size_hint_y=None))
        self.add_widget(MDLabel(text=subtitle, size_hint_y=None))

    def on_touch_up(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_up(touch)
        if self._on_tap:
            self._on_tap(self)
        return True


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
