import json
import ssl

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.network.urlrequest import UrlRequest
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget


# ============================================================
# CONFIG
# ============================================================

WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev"

MODEL = "openai/gpt-4o-mini:online"

SYSTEM_PROMPT = (
    "You are Aizen, a personal AI assistant. "
    "Reply in the same language the user writes in. "
    "If the user writes Hinglish, reply in Hinglish. "
    "Be friendly, clear and concise. "
    "Help the user with normal questions, coding, editing ideas, "
    "learning and everyday tasks. "
    "Do not use markdown formatting."
)


# ============================================================
# SSL
# ============================================================

try:
    import certifi
    CA_FILE = certifi.where()
except Exception:
    CA_FILE = None


# ============================================================
# COLORS
# ============================================================

BG = (0.043, 0.063, 0.125, 1)
SURFACE = (0.09, 0.13, 0.25, 1)
SURFACE_DOWN = (0.13, 0.18, 0.33, 1)

ACCENT = (0.30, 0.55, 1.0, 1)
ACCENT_DOWN = (0.22, 0.43, 0.85, 1)

GREEN = (0.24, 0.86, 0.59, 1)
AMBER = (1.0, 0.76, 0.28, 1)
RED = (1.0, 0.38, 0.38, 1)


# ============================================================
# BUTTON
# ============================================================

class Pill(Button):

    fill = ListProperty(SURFACE)
    fill_down = ListProperty(SURFACE_DOWN)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)

        self.bind(
            pos=self._draw,
            size=self._draw,
            state=self._draw
        )

    def _draw(self, *args):

        self.canvas.before.clear()

        with self.canvas.before:

            Color(
                rgba=self.fill_down
                if self.state == "down"
                else self.fill
            )

            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.height / 2]
            )


# ============================================================
# AIZEN ORB
# ============================================================

class Orb(Widget):

    angle = NumericProperty(0)
    thinking = BooleanProperty(False)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.time = 0

        self.bind(
            pos=self.draw,
            size=self.draw,
            angle=self.draw
        )

        Clock.schedule_interval(
            self.tick,
            1 / 30
        )

    def tick(self, dt):

        self.time += dt

        speed = 260 if self.thinking else 45

        self.angle = (
            self.angle + speed * dt
        ) % 360

    def draw(self, *args):

        self.canvas.clear()

        cx, cy = self.center

        radius = min(
            self.width,
            self.height
        ) / 2

        if radius <= 0:
            return

        import math

        pulse = (
            0.5
            + 0.5
            * math.sin(
                self.time * (
                    6 if self.thinking else 2
                )
            )
        )

        with self.canvas:

            Color(
                0.30,
                0.55,
                1,
                0.07
            )

            Ellipse(
                pos=(
                    cx - radius,
                    cy - radius
                ),
                size=(
                    radius * 2,
                    radius * 2
                )
            )

            Color(
                0.30,
                0.55,
                1,
                0.12
            )

            r2 = radius * 0.80

            Ellipse(
                pos=(
                    cx - r2,
                    cy - r2
                ),
                size=(
                    r2 * 2,
                    r2 * 2
                )
            )

            Color(
                0.06,
                0.09,
                0.18,
                1
            )

            r3 = radius * 0.62

            Ellipse(
                pos=(
                    cx - r3,
                    cy - r3
                ),
                size=(
                    r3 * 2,
                    r3 * 2
                )
            )

            Color(
                0.30,
                0.55,
                1,
                0.30
            )

            Line(
                circle=(
                    cx,
                    cy,
                    radius * 0.70
                ),
                width=dp(1.2)
            )

            Color(
                0.50,
                0.74,
                1,
                1
            )

            Line(
                circle=(
                    cx,
                    cy,
                    radius * 0.70,
                    self.angle,
                    self.angle + 80
                ),
                width=dp(2.4)
            )

            Color(
                0.45,
                0.70,
                1,
                0.55 + 0.35 * pulse
            )

            r4 = radius * (
                0.14 + 0.03 * pulse
            )

            Ellipse(
                pos=(
                    cx - r4,
                    cy - r4
                ),
                size=(
                    r4 * 2,
                    r4 * 2
                )
            )


# ============================================================
# CHAT BUBBLE
# ============================================================

class Bubble(BoxLayout):

    text = StringProperty("")
    mine = BooleanProperty(False)


# ============================================================
# KV UI
# ============================================================

KV = """

<Bubble>:

    orientation: "horizontal"

    size_hint_y: None

    height: message.height + dp(26)

    padding: dp(16), dp(5)

    BoxLayout:

        id: bubble_box

        orientation: "vertical"

        size_hint_x: None

        width: min(
            root.width * 0.78,
            message.texture_size[0] + dp(30)
        )

        padding: dp(14), dp(10)

        canvas.before:

            Color:

                rgba:
                    (0.30, 0.55, 1, 1) \
                    if root.mine \
                    else (0.11, 0.15, 0.28, 1)

            RoundedRectangle:

                pos: self.pos

                size: self.size

                radius: [dp(18)]

        Label:

            id: message

            text: root.text

            font_size: sp(15)

            color: 1, 1, 1, 1

            halign: "left"

            valign: "middle"

            text_size: min(
                root.width * 0.70,
                dp(280)
            ), None

            size_hint_y: None

            height: self.texture_size[1]


<Root>:

    orientation: "vertical"

    canvas.before:

        Color:

            rgba: 0.043, 0.063, 0.125, 1

        Rectangle:

            pos: self.pos

            size: self.size


    # ========================================================
    # TOP BAR
    # ========================================================

    BoxLayout:

        size_hint_y: None

        height: dp(64)

        padding: dp(20), dp(8)

        spacing: dp(8)


        BoxLayout:

            orientation: "vertical"


            Label:

                text: "Aizen"

                bold: True

                font_size: sp(22)

                color: 0.91, 0.93, 0.97, 1

                halign: "left"

                valign: "bottom"

                text_size: self.size


            Label:

                text: "Personal assistant"

                font_size: sp(12)

                color: 0.54, 0.58, 0.70, 1

                halign: "left"

                valign: "top"

                text_size: self.size


        AnchorLayout:

            size_hint_x: None

            width: dp(110)

            anchor_x: "right"

            anchor_y: "center"


            BoxLayout:

                size_hint: None, None

                size: dp(104), dp(32)

                padding: dp(10), 0

                spacing: dp(7)

                canvas.before:

                    Color:

                        rgba: 0.09, 0.13, 0.25, 1

                    RoundedRectangle:

                        pos: self.pos

                        size: self.size

                        radius: [dp(16)]


                Widget:

                    size_hint: None, None

                    size: dp(8), dp(8)

                    pos_hint:
                        {"center_y": 0.5}

                    canvas:

                        Color:

                            rgba: root.status_color

                        Ellipse:

                            pos: self.pos

                            size: self.size


                Label:

                    text: root.status

                    font_size: sp(12)

                    color: 0.91, 0.93, 0.97, 1

                    halign: "left"

                    valign: "middle"

                    text_size: self.size


    # ========================================================
    # ORB
    # ========================================================

    FloatLayout:

        size_hint_y: None

        height: root.orb_height


        Orb:

            id: orb

            size_hint: None, None

            size:
                root.orb_height - dp(16), \
                root.orb_height - dp(16)

            pos_hint:
                {"center_x": 0.5, "center_y": 0.5}


    # ========================================================
    # QUICK BUTTONS
    # ========================================================

    ScrollView:

        size_hint_y: None

        height: dp(50)

        do_scroll_y: False

        bar_width: 0


        BoxLayout:

            size_hint_x: None

            width: self.minimum_width

            padding: dp(20), dp(7)

            spacing: dp(8)


            Pill:

                text: "Search"

                size_hint_x: None

                width: dp(82)

                on_release:
                    root.use_prompt(
                    "Search the web for "
                    )


            Pill:

                text: "Edit"

                size_hint_x: None

                width: dp(70)

                on_release:
                    root.use_prompt(
                    "Help me edit "
                    )


            Pill:

                text: "Write"

                size_hint_x: None

                width: dp(70)

                on_release:
                    root.use_prompt(
                    "Write "
                    )


            Pill:

                text: "Explain"

                size_hint_x: None

                width: dp(82)

                on_release:
                    root.use_prompt(
                    "Explain "
                    )


    # ========================================================
    # CHAT
    # ========================================================

    ScrollView:

        id: scroll

        do_scroll_x: False

        bar_width: dp(3)

        bar_color: 0.30, 0.55, 1, 0.5


        BoxLayout:

            id: chat

            orientation: "vertical"

            size_hint_y: None

            height: self.minimum_height

            padding: 0, dp(8)

            spacing: dp(4)


    # ========================================================
    # INPUT
    # ========================================================

    BoxLayout:

        size_hint_y: None

        height: dp(72)

        padding: dp(14), dp(12)

        spacing: dp(8)


        TextInput:

            id: inp

            hint_text: "Message Aizen"

            multiline: False

            write_tab: False

            font_size: sp(15)

            background_normal: ""

            background_active: ""

            background_color: 0, 0, 0, 0

            foreground_color: 0.91, 0.93, 0.97, 1

            hint_text_color: 0.45, 0.50, 0.65, 1

            cursor_color: 0.30, 0.55, 1, 1

            padding:
                dp(18),
                dp(13),
                dp(18),
                dp(0)

            on_text_validate:
                root.send()

            canvas.before:

                Color:

                    rgba: 0.09, 0.13, 0.25, 1

                RoundedRectangle:

                    pos: self.pos

                    size: self.size

                    radius: [dp(24)]


        Pill:

            text: "Mic"

            size_hint_x: None

            width: dp(55)

            on_release:
                root.on_mic()


        Pill:

            text: "Send"

            bold: True

            size_hint_x: None

            width: dp(70)

            fill: 0.30, 0.55, 1, 1

            fill_down: 0.22, 0.43, 0.85, 1

            color: 1, 1, 1, 1

            on_release:
                root.send()

"""


# ============================================================
# ROOT
# ============================================================

class Root(BoxLayout):

    orb_height = NumericProperty(dp(190))

    status = StringProperty("Online")

    status_color = ListProperty(GREEN)

    busy = BooleanProperty(False)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.history = []

        self.typing_bubble = None

    # --------------------------------------------------------
    # GREETING
    # --------------------------------------------------------

    def greet(self, *args):

        self.add_bubble(
            "Hi bhai! I'm Aizen. Ask me anything.",
            False
        )

    # --------------------------------------------------------
    # ADD MESSAGE
    # --------------------------------------------------------

    def add_bubble(self, text, mine=False):

        bubble = Bubble(
            text=str(text),
            mine=mine
        )

        self.ids.chat.add_widget(
            bubble
        )

        Clock.schedule_once(
            self.scroll_bottom,
            0.1
        )

        return bubble

    # --------------------------------------------------------
    # SCROLL
    # --------------------------------------------------------

    def scroll_bottom(self, *args):

        self.ids.scroll.scroll_y = 0

    # --------------------------------------------------------
    # QUICK PROMPT
    # --------------------------------------------------------

    def use_prompt(self, text):

        self.ids.inp.text = text

        self.ids.inp.focus = True

        Clock.schedule_once(
            lambda dt: setattr(
                self.ids.inp,
                "cursor",
                (len(text), 0)
            ),
            0.1
        )

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    def set_state(
        self,
        busy,
        status=None,
        color=None
    ):

        self.busy = busy

        self.ids.orb.thinking = busy

        if busy:

            self.status = "Thinking"

            self.status_color = AMBER

        else:

            self.status = status or "Online"

            self.status_color = color or GREEN

    # --------------------------------------------------------
    # SMALLER ORB
    # --------------------------------------------------------

    def shrink_orb(self):

        if self.orb_height > dp(100):

            Animation(
                orb_height=dp(100),
                duration=0.3,
                t="out_cubic"
            ).start(self)

    # --------------------------------------------------------
    # MICROPHONE
    # --------------------------------------------------------

    def on_mic(self):

        self.add_bubble(
            "Voice input isn't connected in this build yet.",
            False
        )

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    def send(self):

        box = self.ids.inp

        message = box.text.strip()

        if not message:
            return

        if self.busy:
            return

        box.text = ""

        self.shrink_orb()

        self.add_bubble(
            message,
            True
        )

        self.typing_bubble = self.add_bubble(
            "Thinking...",
            False
        )

        self.set_state(True)

        self.history.append(
            {
                "role": "user",
                "content": message
            }
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        messages.extend(
            self.history[-12:]
        )

        payload = {
            "model": MODEL,
            "messages": messages
        }

        body = json.dumps(payload)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AizenAI/1.0"
        }

        try:

            UrlRequest(
                WORKER_URL,
                req_body=body,
                req_headers=headers,
                timeout=60,
                ca_file=CA_FILE,
                on_success=self.on_success,
                on_failure=self.on_failure,
                on_error=self.on_error
            )

        except Exception as error:

            self.finish(
                "Request start error: %s" % error,
                False
            )

    # --------------------------------------------------------
    # REMOVE THINKING
    # --------------------------------------------------------

    def remove_typing(self):

        if self.typing_bubble is not None:

            try:

                self.ids.chat.remove_widget(
                    self.typing_bubble
                )

            except Exception:
                pass

            self.typing_bubble = None

    # --------------------------------------------------------
    # FINISH
    # --------------------------------------------------------

    def finish(self, text, success=True):

        self.remove_typing()

        self.add_bubble(
            text,
            False
        )

        if success:

            self.history.append(
                {
                    "role": "assistant",
                    "content": text
                }
            )

            self.set_state(
                False,
                "Online",
                GREEN
            )

        else:

            self.set_state(
                False,
                "Error",
                RED
            )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    def on_success(self, request, result):

        try:

            if isinstance(
                result,
                bytes
            ):

                result = result.decode(
                    "utf-8"
                )

            if isinstance(
                result,
                str
            ):

                result = json.loads(
                  
