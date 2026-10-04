# aizen_ui.py  -  PART 1: colors, Orb, Bubble, Pill (layout is in aizen_kv.py)
import math

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

BG = (0.043, 0.063, 0.125, 1)
SURFACE = (0.09, 0.13, 0.25, 1)
SURFACE_DOWN = (0.13, 0.18, 0.33, 1)
ACCENT = (0.30, 0.55, 1.0, 1)
ACCENT_DOWN = (0.22, 0.43, 0.85, 1)
GREEN = (0.24, 0.86, 0.59, 1)
AMBER = (1.0, 0.76, 0.28, 1)
RED = (1.0, 0.38, 0.38, 1)


class Pill(Button):
    fill = ListProperty(SURFACE)
    fill_down = ListProperty(SURFACE_DOWN)


class Orb(Widget):
    angle = NumericProperty(0)
    thinking = BooleanProperty(False)
    listening = BooleanProperty(False)
    speaking = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0.0
        self.bind(pos=self._draw, size=self._draw, angle=self._draw)
        self.bind(
            thinking=self._draw,
            listening=self._draw,
            speaking=self._draw,
        )
        Clock.schedule_interval(self._tick, 1 / 30.0)

    def _tick(self, dt):
        self._t += dt

        if self.listening:
            speed = 260
        elif self.thinking:
            speed = 320
        elif self.speaking:
            speed = 190
        else:
            speed = 45

        self.angle = (self.angle + speed * dt) % 360

    def _draw(self, *args):
        self.canvas.clear()

        cx, cy = self.center
        r = min(self.width, self.height) / 2.0

        if r <= 0:
            return

        pulse_speed = 8 if (
            self.thinking or self.listening or self.speaking
        ) else 2

        pulse = 0.5 + 0.5 * math.sin(self._t * pulse_speed)

        if self.listening:
            outer = (0.30, 0.86, 0.70)
        elif self.speaking:
            outer = (0.55, 0.42, 1.0)
        else:
            outer = (0.30, 0.55, 1.0)

        with self.canvas:
            Color(outer[0], outer[1], outer[2], 0.08 + 0.05 * pulse)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))

            Color(outer[0], outer[1], outer[2], 0.14 + 0.05 * pulse)
            rr = r * (0.80 + 0.03 * pulse)
            Ellipse(pos=(cx - rr, cy - rr), size=(2 * rr, 2 * rr))

            Color(0.06, 0.09, 0.18, 1)
            rr = r * 0.62
            Ellipse(pos=(cx - rr, cy - rr), size=(2 * rr, 2 * rr))

            Color(outer[0], outer[1], outer[2], 0.30)
            Line(circle=(cx, cy, r * 0.70), width=dp(1.2))

            Color(
                min(outer[0] + 0.20, 1),
                min(outer[1] + 0.20, 1),
                min(outer[2] + 0.20, 1),
                1,
            )
            Line(
                circle=(cx, cy, r * 0.70, self.angle, self.angle + 85),
                width=dp(2.6),
                cap="round",
            )

            Color(
                min(outer[0] + 0.15, 1),
                min(outer[1] + 0.15, 1),
                min(outer[2] + 0.15, 1),
                0.60 + 0.35 * pulse,
            )
            rc = r * (0.14 + 0.04 * pulse)
            Ellipse(pos=(cx - rc, cy - rc), size=(2 * rc, 2 * rc))


class Bubble(BoxLayout):
    text = StringProperty("")
    mine = BooleanProperty(False)

from aizen_kv import KV  # noqa: E402,F401
