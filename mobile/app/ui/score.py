from __future__ import annotations

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

from .base import BaseScreen


class ScoreScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.item_id: str | None = None
        self.item_code: str | None = None
        self.selected_n = 0
        self.n_value = 0
        self._hydrated = False
        self._value_labels: dict[str, MDLabel] = {}

        self.topbar: MDTopAppBar | None = None
        self.item_label: MDLabel | None = None
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
        self.loading_label: MDLabel | None = None
        self.save_btn: MDRaisedButton | None = None
        self.others_btn: MDIconButton | None = None
        self._others_dialog: MDDialog | None = None

        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="16dp", spacing="12dp")

        self.topbar = MDTopAppBar(
            title="Puntuar",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["account-group", lambda x: self.on_view_others()]],
        )
        root.add_widget(self.topbar)

        self.item_label = MDLabel(
            text="Item",
            halign="center",
            font_style="H5",
            size_hint_y=None,
        )
        self.item_label.bind(texture_size=lambda *_: setattr(self.item_label, "height", self.item_label.texture_size[1]))
        root.add_widget(self.item_label)

        self.val_a = self._add_slider_row(root, "A")
        self.slider_a = self._add_slider(root, "a")
        self.val_b = self._add_slider_row(root, "B")
        self.slider_b = self._add_slider(root, "b")
        self.val_c = self._add_slider_row(root, "C")
        self.slider_c = self._add_slider(root, "c")
        self.val_d = self._add_slider_row(root, "D")
        self.slider_d = self._add_slider(root, "d")

        n_label = MDLabel(text="N", size_hint_y=None)
        n_label.bind(texture_size=lambda *_: setattr(n_label, "height", n_label.texture_size[1]))
        root.add_widget(n_label)

        n_box = MDBoxLayout(spacing="8dp", size_hint_y=None)
        n_box.height = 48
        self.n0_btn = MDRaisedButton(text="0", on_release=lambda *_: self.set_n(0))
        self.n1_btn = MDRaisedButton(text="1", on_release=lambda *_: self.set_n(1))
        self.n2_btn = MDRaisedButton(text="2", on_release=lambda *_: self.set_n(2))
        n_box.add_widget(self.n0_btn)
        n_box.add_widget(self.n1_btn)
        n_box.add_widget(self.n2_btn)
        root.add_widget(n_box)

        self.loading_label = MDLabel(
            text="Guardando...",
            halign="center",
            size_hint_y=None,
        )
        self.loading_label.bind(texture_size=lambda *_: setattr(self.loading_label, "height", self.loading_label.texture_size[1]))
        self.loading_label.opacity = 0
        root.add_widget(self.loading_label)

        self.save_btn = MDRaisedButton(text="GUARDAR", pos_hint={"center_x": 0.5}, on_release=lambda *_: self.on_save())
        root.add_widget(self.save_btn)

        self.add_widget(root)
        self._set_n_styles()

    def _add_slider_row(self, root: MDBoxLayout, label: str) -> MDLabel:
        row = MDBoxLayout(size_hint_y=None)
        row.height = 28
        row.add_widget(MDLabel(text=label))
        value_label = MDLabel(text=f"{label}: 0", halign="right")
        row.add_widget(value_label)
        root.add_widget(row)
        self._value_labels[label.lower()] = value_label
        return value_label

    def _add_slider(self, root: MDBoxLayout, key: str) -> MDSlider:
        slider = MDSlider(min=0, max=10, value=0, step=1)
        slider.bind(value=lambda _s, v: self.update_value(key, v))
        root.add_widget(slider)
        return slider

    def set_item(self, item_id: str, item_code: str, prefill_rating: dict | None = None):
        self.item_id = item_id
        self.item_code = item_code
        self._hydrated = False
        if self.item_label:
            self.item_label.text = f"Item: {item_code}"
        if self.topbar:
            self.topbar.title = f"Puntuar {item_code}"
        if prefill_rating:
            a = int(prefill_rating.get("a", 0))
            b = int(prefill_rating.get("b", 0))
            c = int(prefill_rating.get("c", 0))
            d = int(prefill_rating.get("d", 0))
            n = int(prefill_rating.get("n", 0))
            self.hydrate_values(a, b, c, d, n)

    def go_back(self):
        self.manager.current = "items"

    def update_value(self, key: str, value: float):
        text_value = str(int(round(value)))
        label = self._value_labels.get(key)
        if label:
            label.text = f"{key.upper()}: {text_value}"

    def set_n(self, value: int):
        self.selected_n = int(value)
        self.n_value = int(value)
        self._set_n_styles()

    def hydrate_values(self, a: int, b: int, c: int, d: int, n: int) -> None:
        if self._hydrated:
            return
        if self.slider_a:
            self.slider_a.value = a
        if self.slider_b:
            self.slider_b.value = b
        if self.slider_c:
            self.slider_c.value = c
        if self.slider_d:
            self.slider_d.value = d
        self.set_n(n)
        self._hydrated = True

    def _set_n_styles(self):
        app = MDApp.get_running_app()
        theme = app.theme_cls if app else None
        buttons = {0: self.n0_btn, 1: self.n1_btn, 2: self.n2_btn}
        for n, btn in buttons.items():
            if not btn:
                continue
            if n == self.selected_n:
                if theme:
                    btn.md_bg_color = theme.primary_color
            else:
                if theme:
                    btn.md_bg_color = theme.disabled_hint_text_color

    def on_save(self):
        if not self.item_id:
            self.show_error("Item invalido")
            return
        if not all([self.slider_a, self.slider_b, self.slider_c, self.slider_d]):
            self.show_error("UI incompleta")
            return

        a = int(round(self.slider_a.value))
        b = int(round(self.slider_b.value))
        c = int(round(self.slider_c.value))
        d = int(round(self.slider_d.value))
        n = int(self.n_value)
        if any(v < 0 or v > 10 for v in (a, b, c, d)) or n not in (0, 1, 2):
            self.show_error("Valores fuera de rango")
            return

        self._set_loading(True)

        def _do():
            return self.manager.app.api.create_rating(self.item_id, a, b, c, d, n)

        def _ok(_data):
            self.show_info("Guardado")
            self._set_loading(False)
            detail = self.manager.get_screen("item_detail")
            if hasattr(detail, "refresh"):
                detail.refresh()
            self.manager.current = "item_detail"

        def _err(message: str):
            if self.handle_session_error(message):
                return
            if "COOLDOWN_RATING_5MIN" in message:
                self.show_error("Espera 5 minutos para volver a puntuar este item")
                self._set_loading(False)
                return
            if "No se puede conectar" in message:
                self.show_error("Servidor no disponible")
            else:
                self.show_error(message)
            self._set_loading(False)

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def on_view_others(self):
        if not self.item_id:
            self.show_error("Item inválido")
            return

        def _do():
            return self.manager.app.api.get_others(self.item_id)

        def _ok(data):
            self._show_others_dialog(data or {})

        def _err(message: str):
            if self.handle_session_error(message):
                return
            if "RATE_FIRST_TO_VIEW_OTHERS" in message:
                self.show_error("Puntúa primero para ver a los demás")
                return
            if "No se puede conectar" in message:
                self.show_error("Servidor no disponible")
                return
            self.show_error(message)

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def _show_others_dialog(self, data: dict):
        if self._others_dialog:
            self._others_dialog.dismiss()
            self._others_dialog = None

        count = data.get("others_count", 0)
        avg = data.get("others_avg") or {}
        best = data.get("others_best") or {}
        last = data.get("others_last") or []

        content = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None)
        content.height = 320

        header = MDLabel(text=f"Otros ({count})", halign="center", font_style="H5", size_hint_y=None)
        header.bind(texture_size=lambda *_: setattr(header, "height", header.texture_size[1]))
        content.add_widget(header)

        def _line(label: str, val: dict):
            text = f"{label} A:{val.get('a','-')} B:{val.get('b','-')} C:{val.get('c','-')} D:{val.get('d','-')} N:{val.get('n','-')} T:{val.get('total','-')}"
            lbl = MDLabel(text=text, size_hint_y=None)
            lbl.bind(texture_size=lambda *_: setattr(lbl, "height", lbl.texture_size[1]))
            return lbl

        content.add_widget(_line("Prom", avg))
        content.add_widget(_line("Mejor", best))

        content.add_widget(MDLabel(text="Últimas", size_hint_y=None))
        for r in last[:10]:
            profile = r.get("profile", "?")
            total = r.get("total", "-")
            created = (r.get("created_at") or "")[:19].replace("T", " ")
            row = MDLabel(text=f"P{profile}  T:{total}  {created}", size_hint_y=None)
            row.bind(texture_size=lambda *_: setattr(row, "height", row.texture_size[1]))
            content.add_widget(row)

        self._others_dialog = MDDialog(title="Votos de otros", type="custom", content_cls=content, buttons=[])
        self._others_dialog.open()

    def _set_loading(self, is_loading: bool):
        if self.loading_label:
            self.loading_label.opacity = 1 if is_loading else 0
            self.loading_label.height = self.loading_label.texture_size[1] if is_loading else 0
        if self.save_btn:
            self.save_btn.disabled = is_loading
