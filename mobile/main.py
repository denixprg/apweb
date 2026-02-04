from __future__ import annotations

from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager

from app.core.api import ApiClient
from app.core.pin import PinStore
from app.ui.auth import LoginScreen
from app.ui.items import ItemsScreen
from app.ui.score import ScoreScreen
from app.ui.summary import SummaryScreen
from app.ui.profile import ProfileSelectScreen
from app.ui.item_detail import ItemDetailScreen

Window.size = (420, 800)


class RatingApp(MDApp):
    def build(self):
        self.title = "Rating App"
        self.theme_cls.primary_palette = "Blue"
        self.api = ApiClient()
        self.pin_store = PinStore(self.user_data_dir)
        self._pin_dialog = None
        Window.bind(on_focus=self._on_focus_change)

        sm = ScreenManager()
        sm.app = self
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(ItemsScreen(name="items"))
        sm.add_widget(ScoreScreen(name="score"))
        sm.add_widget(ItemDetailScreen(name="item_detail"))
        sm.add_widget(SummaryScreen(name="summary"))
        sm.add_widget(ProfileSelectScreen(name="profile_select"))
        sm.current = "profile_select"
        return sm

    def on_pause(self):
        self.lock_names()
        return True

    def _on_focus_change(self, _window, focused: bool):
        if not focused:
            self.lock_names()

    def lock_names(self):
        screen = self.root.get_screen("items")
        screen.hide_names()

    def _dismiss_pin_dialog(self):
        if self._pin_dialog:
            self._pin_dialog.dismiss()
            self._pin_dialog = None


if __name__ == "__main__":
    RatingApp().run()
