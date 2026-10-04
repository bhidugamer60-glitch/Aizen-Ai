# main.py  -  PART 4: the Root screen and the App
# (needs aizen_ui.py, aizen_voice.py and aizen_chat.py in the same folder)
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform

from aizen_ui import (  # noqa: F401
    ACCENT, AMBER, BG, GREEN, RED, KV, Bubble, Orb, Pill,
)

if platform == "android":
    from android.permissions import request_permissions, Permission

from aizen_voice import VoiceMixin
from aizen_chat import ChatMixin


class Root(VoiceMixin, ChatMixin, BoxLayout):
    orb_h = NumericProperty(dp(190))
    status = StringProperty("Online")
    status_color = ListProperty(GREEN)
    busy = BooleanProperty(False)
    call_active = BooleanProperty(False)
    subtitle = StringProperty("Personal assistant")
    orb_label = StringProperty("Aizen AI")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = []
        self.compact = False
        self._typing = None
        self._init_voice()

    def greet(self, *args):
        self.add_bubble(
            "Hi, I'm Aizen. Tap Call for voice conversation, "
            "or send me a message.",
            mine=False
        )

    def add_bubble(self, text, mine):
        b = Bubble(text=str(text), mine=mine)
        self.ids.chat.add_widget(b)
        Clock.schedule_once(self._scroll_down, 0.08)
        return b

    def _scroll_down(self, *args):
        self.ids.scroll.scroll_y = 0

    def use_prompt(self, prefix):
        box = self.ids.inp
        box.text = prefix
        box.focus = True

        Clock.schedule_once(
            lambda dt: setattr(box, "cursor", (len(prefix), 0)),
            0.1
        )

    def set_state(self, busy, label=None, color=None):
        self.busy = busy
        self.ids.orb.thinking = busy

        if busy:
            self.status = "Thinking"
            self.status_color = AMBER
            self.orb_label = "Aizen is thinking..."
        else:
            self.status = label or "Online"
            self.status_color = color or GREEN
            self.orb_label = "Aizen AI"

    def shrink_orb(self):
        if not self.compact:
            self.compact = True
            Animation(orb_h=dp(112), duration=0.35, t="out_cubic").start(self)


class AizenApp(App):
    title = "Aizen"

    def build(self):
        Window.clearcolor = BG
        Window.softinput_mode = "below_target"
        Builder.load_string(KV)
        self.root_widget = Root()
        Clock.schedule_once(self.root_widget.greet, 0.3)
        return self.root_widget

    def on_start(self):
        if platform == "android":
            request_permissions(
                [Permission.RECORD_AUDIO],
                self._on_permissions
            )

    def _on_permissions(self, permissions, grants):
        if grants and all(grants):
            self.root_widget._setup_android_voice()

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        try:
            self.root_widget.end_call()
        except Exception:
            pass


if __name__ == "__main__":
    AizenApp().run()
