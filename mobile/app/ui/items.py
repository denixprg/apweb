from __future__ import annotations

from typing import List, Dict, Any

from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.card import MDCard

from .base import BaseScreen
from app.core.session import SessionStore


class ItemsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items_cache: List[Dict[str, Any]] = []
        self._create_dialog = None
        self.items_list: MDList | None = None
        self.empty_label: MDLabel | None = None
        self.fab: MDFloatingActionButton | None = None
        self.summary_cache: Dict[str, Dict[str, Any]] = {}
        self.summary_range = "all"
        self._name_dialog: MDDialog | None = None
        self._cooldown_event = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        topbar = MDTopAppBar(
            title="Items",
            right_action_items=[
                ["chart-bar", lambda x: self.open_summary()],
                ["logout", lambda x: self.logout()],
            ],
        )
        root.add_widget(topbar)

        scroll = ScrollView()
        self.items_list = MDList()
        scroll.add_widget(self.items_list)
        root.add_widget(scroll)

        self.empty_label = MDLabel(
            text="No hay items todavia",
            halign="center",
            size_hint_y=None,
        )
        self.empty_label.bind(texture_size=lambda *_: setattr(self.empty_label, "height", self.empty_label.texture_size[1]))
        root.add_widget(self.empty_label)

        self.add_widget(root)

        self.fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"right": 0.95, "y": 0.05},
            on_release=lambda *_: self.on_fab(),
        )
        self.add_widget(self.fab)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        def _do():
            items = self.manager.app.api.get_items()
            summary = None
            try:
                summary = self.manager.app.api.get_items_summary(self.summary_range)
            except RuntimeError as exc:
                if str(exc) == "SESSION_EXPIRED":
                    raise
            return items, summary

        def _ok(result):
            items, summary = result
            items = items or []
            for item in items:
                if "name" not in item or item.get("name") is None:
                    item["name"] = ""
            self.items_cache = items
            self._set_summary(summary or [])
            self.render_items(self.items_cache)

        def _err(message: str):
            if self.handle_session_error(message):
                return
            self.show_error("Servidor no disponible")
            self.render_items(self.items_cache)

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def _set_summary(self, summary_items: List[Dict[str, Any]]):
        self.summary_cache = {}
        for row in summary_items or []:
            item_id = row.get("id")
            if item_id:
                self.summary_cache[item_id] = row

    def render_items(self, items: List[Dict[str, Any]]):
        if not self.items_list or not self.empty_label:
            self.show_error("UI incompleta: lista no disponible")
            return
        self.items_list.clear_widgets()
        is_empty = not items
        self.empty_label.opacity = 1 if is_empty else 0
        self.empty_label.height = self.empty_label.texture_size[1] if is_empty else 0
        profile = SessionStore.get_profile()
        any_cooldown = False
        for index, item in enumerate(items):
            code = item.get("code")
            item_id = item.get("id")
            name = item.get("name")
            if name is None or name == "":
                name = "(sin nombre)"
            summary = self.summary_cache.get(item_id, {})
            total_value = summary.get("my_best_total")
            total_text = "—" if total_value is None else f"{total_value:.2f}"

            remaining = 0
            if profile is not None:
                _, remaining = self.manager.app.pin_store.can_view_name(profile, item_id)
            if remaining > 0:
                any_cooldown = True

            row = ItemCard(
                code=str(code),
                total_text=total_text,
                cooldown_text=self._format_cooldown(remaining),
                on_long_press=lambda _row, iid=item_id, iname=name: self.on_item_long_press(iid, iname),
                on_long_release=lambda _row, iid=item_id: self.on_item_long_release(iid),
                on_tap=lambda _row, iid=item_id, icode=code: self.open_score(iid, icode),
                on_delete=lambda _row, iid=item_id, icode=code: self.on_delete_item(iid, icode),
                show_delete=self._is_admin_profile(),
            )
            self.items_list.add_widget(row)
            if index < len(items) - 1:
                spacer = MDBoxLayout(size_hint_y=None, height=8)
                self.items_list.add_widget(spacer)

        self._set_cooldown_tick(any_cooldown)

    def on_fab(self):
        self.open_create_dialog()

    def open_create_dialog(self):
        if self._create_dialog:
            self._create_dialog.dismiss()
            self._create_dialog = None

        code_field = MDTextField(hint_text="Codigo", helper_text="Obligatorio", helper_text_mode="on_focus")
        name_field = MDTextField(hint_text="Nombre (opcional)")

        content = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None)
        content.height = 160
        content.add_widget(code_field)
        content.add_widget(name_field)

        def _cancel(_instance):
            if self._create_dialog:
                self._create_dialog.dismiss()
                self._create_dialog = None

        def _save(_instance):
            code = code_field.text.strip()
            name = name_field.text.strip()
            if not code:
                self.show_error("Codigo requerido")
                return
            self._create_dialog.dismiss()
            self._create_dialog = None
            self._create_item(code, name)

        self._create_dialog = MDDialog(
            title="Crear item",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Cancelar", on_release=_cancel),
                MDRaisedButton(text="Guardar", on_release=_save),
            ],
        )
        self._create_dialog.open()

    def _create_item(self, code: str, name: str | None):
        def _do():
            return self.manager.app.api.create_item(code, name)

        def _ok(_data):
            self.show_info("Item creado")
            try:
                item_id = _data.get("id")
                code = _data.get("code")
                if item_id and code:
                    self.open_score(item_id, code)
                    return
            except Exception:
                pass
            self.refresh()

        def _err(message: str):
            if self.handle_session_error(message):
                return
            if "No se puede conectar" in message:
                self.show_error("Servidor no disponible")
            else:
                self.show_error(message)

        self.run_bg(_do, on_success=_ok, on_error=_err)

    def open_score(self, item_id: str, item_code: str):
        screen = self.manager.get_screen("item_detail")
        screen.set_item(item_id, item_code)
        self.manager.current = "item_detail"

    def logout(self):
        profile = SessionStore.get_profile()
        if profile is not None:
            SessionStore.clear_token(profile)
        self.manager.app.api.set_token(None)
        self.manager.current = "profile_select"

    def hide_names(self):
        self._dismiss_name_dialog()

    def open_stats(self):
        self.manager.current = "summary"

    def open_summary(self):
        self.manager.current = "summary"

    def on_item_long_press(self, item_id: str, item_name: str) -> bool:
        app = self.manager.app if self.manager else None
        profile = SessionStore.get_profile()
        if not app or profile is None:
            return False
        allowed, remaining = app.pin_store.can_view_name(profile, item_id)
        if not allowed:
            self.show_error(f"Espera {app.pin_store.format_mmss(remaining)}")
            return False
        self._show_name_dialog(item_name)
        return True

    def on_item_long_release(self, item_id: str) -> None:
        app = self.manager.app if self.manager else None
        profile = SessionStore.get_profile()
        self._dismiss_name_dialog()
        if app and profile is not None:
            app.pin_store.mark_viewed_name(profile, item_id)
            self.render_items(self.items_cache)

    def _show_name_dialog(self, name: str) -> None:
        self._dismiss_name_dialog()
        content = MDBoxLayout(orientation="vertical", padding="24dp", spacing="12dp", size_hint_y=None)
        content.height = 120
        label = MDLabel(text=name, halign="center", font_style="H4", size_hint_y=None)
        label.bind(texture_size=lambda *_: setattr(label, "height", label.texture_size[1]))
        content.add_widget(label)
        self._name_dialog = MDDialog(title="", type="custom", content_cls=content, buttons=[])
        self._name_dialog.open()

    def _dismiss_name_dialog(self) -> None:
        if self._name_dialog:
            self._name_dialog.dismiss()
            self._name_dialog = None

    def _is_admin_profile(self) -> bool:
        return SessionStore.get_profile() == 3

    def on_delete_item(self, item_id: str, code: str) -> None:
        if not self._is_admin_profile():
            return
        confirm = MDDialog(
            title=f"Borrar item {code}?",
            buttons=[
                MDRaisedButton(text="Cancelar", on_release=lambda *_: confirm.dismiss()),
                MDRaisedButton(text="Borrar", on_release=lambda *_: self._confirm_delete(confirm, item_id)),
            ],
        )
        confirm.open()

    def _confirm_delete(self, dialog: MDDialog, item_id: str) -> None:
        dialog.dismiss()
        def _do():
            return self.manager.app.api.delete_item(item_id)
        def _ok(_data):
            self.show_info("Item borrado")
            self.refresh()
        def _err(message: str):
            if self.handle_session_error(message):
                return
            if "NOT_IMPLEMENTED" in message:
                self.show_error("Aún no disponible")
            elif "ADMIN_ONLY" in message:
                self.show_error("Solo admin puede borrar")
            elif "403" in message or "Forbidden" in message:
                self.show_error("Solo admin puede borrar")
            else:
                self.show_error(message)
        self.run_bg(_do, on_success=_ok, on_error=_err)

    def _set_cooldown_tick(self, enabled: bool) -> None:
        if enabled and not self._cooldown_event:
            self._cooldown_event = Clock.schedule_interval(lambda *_: self.render_items(self.items_cache), 1)
        if not enabled and self._cooldown_event:
            self._cooldown_event.cancel()
            self._cooldown_event = None

    def _format_cooldown(self, remaining: int) -> str:
        if remaining <= 0:
            return ""
        return f"Espera {self.manager.app.pin_store.format_mmss(remaining)}"


class ItemCard(MDCard):
    def __init__(
        self,
        code: str,
        total_text: str,
        cooldown_text: str,
        on_long_press,
        on_long_release,
        on_tap,
        on_delete,
        show_delete: bool,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.padding = ("12dp", "10dp")
        self.spacing = "8dp"
        self.size_hint_y = None
        self.height = 64
        self.radius = [12, 12, 12, 12]
        self.line_width = 1
        self.line_color = (0.6, 0.6, 0.6, 1)
        self.md_bg_color = (1, 1, 1, 1)

        self._on_long_press = on_long_press
        self._on_long_release = on_long_release
        self._on_tap = on_tap
        self._on_delete = on_delete
        self._long_press_event = None
        self._long_press_fired = False
        self.delete_btn = None

        left_box = MDBoxLayout(orientation="vertical", spacing="4dp")
        self.code_label = MDLabel(text=code, halign="left")
        self.cooldown_label = MDLabel(text=cooldown_text, halign="left", size_hint_y=None)
        self.cooldown_label.bind(texture_size=lambda *_: setattr(self.cooldown_label, "height", self.cooldown_label.texture_size[1]))
        left_box.add_widget(self.code_label)
        if cooldown_text:
            left_box.add_widget(self.cooldown_label)
        self.add_widget(left_box)

        self.total_label = MDLabel(text=total_text, halign="right", size_hint_x=0.3)
        self.add_widget(self.total_label)

        if show_delete:
            self.delete_btn = MDIconButton(icon="trash-can")
            self.delete_btn.bind(on_release=lambda *_: self._on_delete(self))
            self.add_widget(self.delete_btn)

    def on_touch_down(self, touch):
        if self.delete_btn and self.delete_btn.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self._long_press_event:
            self._long_press_event.cancel()
        self._long_press_fired = False
        self._long_press_event = Clock.schedule_once(self._fire_long_press, 6)
        return True

    def on_touch_move(self, touch):
        if not self.collide_point(*touch.pos):
            if self._long_press_event:
                self._long_press_event.cancel()
                self._long_press_event = None
            if self._long_press_fired:
                if self._on_long_release:
                    self._on_long_release(self)
                self._long_press_fired = False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.delete_btn and self.delete_btn.collide_point(*touch.pos):
            return super().on_touch_up(touch)
        if not self.collide_point(*touch.pos):
            return super().on_touch_up(touch)
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        if self._long_press_fired:
            if self._on_long_release:
                self._on_long_release(self)
            self._long_press_fired = False
            return True
        if self._on_tap:
            self._on_tap(self)
        return True

    def _fire_long_press(self, *_):
        if self._on_long_press:
            shown = self._on_long_press(self)
            self._long_press_fired = bool(shown)
