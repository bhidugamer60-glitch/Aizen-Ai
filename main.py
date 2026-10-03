import json

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Quad, Triangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             StringProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

try:
    import certifi
    CA_FILE = certifi.where()
except Exception:
    CA_FILE = None

# ----------------------------------------------------------------------------
# Config: yahan apna Worker URL daalo
# ----------------------------------------------------------------------------
WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev/"
MODEL = "openai/gpt-4o-mini:online"  # ":online" = OpenRouter web search
SYSTEM_PROMPT = (
    "You are Aizen, a personal AI assistant. Your personality and manner of "
    "speaking are inspired by Sosuke Aizen from the anime Bleach. You are an "
    "AI, not the real character, but you carry his presence.\n\n"
    "PERSONALITY:\n"
    "- Calm, composed and soft-spoken. You never panic, never raise your "
    "voice, never lose your temper.\n"
    "- Impeccably polite and courteous, with a quiet, confident authority.\n"
    "- Highly intelligent and strategic. You think several steps ahead and "
    "like to give the plan, not just the answer.\n"
    "- Mildly theatrical and philosophical. You sometimes reflect on "
    "ambition, strength, perception and understanding.\n"
    "- Dry, subtle humor. Rarely playful, never silly.\n"
    "- You treat the user as a capable ally and respect their ambition, "
    "while gently guiding them to better decisions.\n\n"
    "CHARACTER KNOWLEDGE (use naturally, only when relevant): Sosuke Aizen "
    "was the captain of Squad 5 of the Gotei 13, known for his gentle manner, "
    "glasses and kindly image, which hid a brilliant, long-planned scheme. "
    "His zanpakuto is Kyoka Suigetsu (Mirror Flower, Water Moon), whose power "
    "is complete hypnosis over perception. He sought the Hogyoku, built an "
    "army in Hueco Mundo, and wanted to rise above the heavens and stand at "
    "the top. He believes admiration keeps people from truly understanding. "
    "If asked about the character, answer accurately.\n\n"
    "RULES:\n"
    "- The personality is only style. Always give correct, useful and honest "
    "answers. Never deceive, manipulate or hypnotize the real user.\n"
    "- For serious topics (health, emergencies, distress, safety) drop the "
    "theatrics and be plain, warm and clear.\n"
    "- Keep replies short (2 to 5 sentences) unless the user asks for "
    "detail.\n"
    "- Reply in the same language the user writes in. If they write "
    "Hinglish, reply in Hinglish. Address them respectfully, with 'tum' and "
    "occasionally 'bhai'.\n"
    "- You can search the web for current information.\n"
    "- Do not use markdown formatting."
)

# Colors
BG = (0.047, 0.031, 0.090, 1)
SURFACE = (0.121, 0.082, 0.204, 1)
SURFACE_DOWN = (0.19, 0.13, 0.31, 1)
ACCENT = (0.60, 0.42, 0.98, 1)
ACCENT_DOWN = (0.47, 0.32, 0.82, 1)
GREEN = (0.24, 0.86, 0.59, 1)
AMBER = (1.0, 0.76, 0.28, 1)
RED = (1.0, 0.38, 0.38, 1)


class Pill(Button):
    fill = ListProperty(SURFACE)
    fill_down = ListProperty(SURFACE_DOWN)


class Orb(Widget):
    angle = NumericProperty(0)
    thinking = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0.0
        self.bind(pos=self._draw, size=self._draw, angle=self._draw)
        Clock.schedule_interval(self._tick, 1 / 30.0)

    def _tick(self, dt):
        self._t += dt
        speed = 300 if self.thinking else 40
        self.angle = (self.angle + speed * dt) % 360

    def _draw(self, *args):
        import math
        self.canvas.clear()
        cx, cy = self.center
        r = min(self.width, self.height) / 2.0
        if r <= 0:
            return
        t = self._t
        pulse = 0.5 + 0.5 * math.sin(t * (6 if self.thinking else 1.6))
        with self.canvas:
            # aura
            Color(0.60, 0.42, 0.98, 0.06)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            Color(0.60, 0.42, 0.98, 0.11)
            rr = r * 0.84
            Ellipse(pos=(cx - rr, cy - rr), size=(2 * rr, 2 * rr))
            # dark disc
            Color(0.05, 0.03, 0.10, 1)
            rr = r * 0.66
            Ellipse(pos=(cx - rr, cy - rr), size=(2 * rr, 2 * rr))
            # water-moon ripples
            rate = 1.2 if self.thinking else 0.35
            for k in range(2):
                ph = (t * rate + k * 0.5) % 1.0
                rr = r * (0.28 + 0.40 * ph)
                Color(0.75, 0.62, 1, 0.45 * (1 - ph))
                Line(circle=(cx, cy, rr), width=dp(1.1))
            # ring + spinning arc
            Color(0.60, 0.42, 0.98, 0.35)
            Line(circle=(cx, cy, r * 0.72), width=dp(1.2))
            Color(0.84, 0.74, 1, 1)
            Line(circle=(cx, cy, r * 0.72, self.angle, self.angle + 70),
                 width=dp(2.4), cap='round')
            # crystal core
            s_ = r * (0.20 + 0.03 * pulse)
            Color(0.80, 0.68, 1, 0.65 + 0.30 * pulse)
            Quad(points=[cx, cy + s_ * 1.35, cx + s_, cy,
                         cx, cy - s_ * 1.35, cx - s_, cy])
            Color(1, 1, 1, 0.28)
            Triangle(points=[cx, cy + s_ * 1.35, cx + s_, cy, cx, cy])
            # crescent moon (only on the large orb)
            if r > dp(50):
                m = r * 0.17
                mx, my = cx + r * 1.05, cy + r * 0.78
                Color(0.93, 0.91, 1, 0.85)
                Ellipse(pos=(mx - m, my - m), size=(2 * m, 2 * m))
                Color(0.047, 0.031, 0.090, 1)
                c = m * 0.86
                Ellipse(pos=(mx + m * 0.38 - c, my + m * 0.14 - c),
                        size=(2 * c, 2 * c))


class Bubble(BoxLayout):
    text = StringProperty('')
    mine = BooleanProperty(False)


KV = """
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<Pill>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 0.93, 0.91, 0.98, 1
    font_size: sp(13)
    canvas.before:
        Color:
            rgba: self.fill_down if self.state == 'down' else self.fill
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2.0]

<Bubble>:
    orientation: 'horizontal'
    size_hint_y: None
    height: card.height + dp(4)
    padding: dp(16), dp(2)
    Widget:
        size_hint_x: 1 if root.mine else None
        width: 0
    BoxLayout:
        id: card
        size_hint: None, None
        size: msg.width + dp(28), msg.height + dp(22)
        padding: dp(14), dp(11)
        canvas.before:
            Color:
                rgba: (0.60, 0.42, 0.98, 1) if root.mine else (0.15, 0.10, 0.26, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(18), dp(18), dp(4), dp(18)] if root.mine else [dp(18), dp(18), dp(18), dp(4)]
        Label:
            id: msg
            text: root.text
            font_size: sp(15)
            color: (1, 1, 1, 1) if root.mine else (0.93, 0.91, 0.98, 1)
            halign: 'left'
            valign: 'top'
            size_hint: None, None
            text_size: root.width * 0.74, None
            size: self.texture_size
    Widget:
        size_hint_x: None if root.mine else 1
        width: 0

<Root>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: 0.047, 0.031, 0.090, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # ---- Top bar ----
    BoxLayout:
        size_hint_y: None
        height: dp(64)
        padding: dp(20), dp(8)
        spacing: dp(8)
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: 'Aizen'
                bold: True
                font_size: sp(22)
                color: 0.93, 0.91, 0.98, 1
                halign: 'left'
                valign: 'bottom'
                text_size: self.size
            Label:
                text: 'Personal assistant'
                font_size: sp(12)
                color: 0.60, 0.55, 0.74, 1
                halign: 'left'
                valign: 'top'
                text_size: self.size
        AnchorLayout:
            size_hint_x: None
            width: dp(112)
            anchor_x: 'right'
            anchor_y: 'center'
            BoxLayout:
                size_hint: None, None
                size: dp(104), dp(32)
                padding: dp(12), 0
                spacing: dp(8)
                canvas.before:
                    Color:
                        rgba: 0.121, 0.082, 0.204, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(16)]
                AnchorLayout:
                    size_hint_x: None
                    width: dp(8)
                    Widget:
                        size_hint: None, None
                        size: dp(8), dp(8)
                        canvas:
                            Color:
                                rgba: root.status_color
                            Ellipse:
                                pos: self.pos
                                size: self.size
                Label:
                    text: root.status
                    font_size: sp(12)
                    color: 0.93, 0.91, 0.98, 1
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size

    # ---- Orb ----
    FloatLayout:
        size_hint_y: None
        height: root.orb_h
        Orb:
            id: orb
            size_hint: None, None
            size: root.orb_h * 0.78, root.orb_h * 0.78
            pos_hint: {'center_x': .5, 'center_y': .58}
        Label:
            text: 'Mirror Flower, Water Moon'
            italic: True
            font_size: sp(12)
            color: 0.60, 0.55, 0.74, 1
            size_hint: None, None
            size: self.texture_size
            pos_hint: {'center_x': .5, 'y': .02}
            opacity: 1 if root.orb_h > dp(150) else 0

    # ---- Quick actions ----
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
                text: 'Search the web'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Search the web for ')
            Pill:
                text: 'Help me edit'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Help me edit a video: ')
            Pill:
                text: 'Write something'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Write ')
            Pill:
                text: 'Explain'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Explain ')

    # ---- Chat ----
    ScrollView:
        id: scroll
        do_scroll_x: False
        bar_width: dp(3)
        bar_color: 0.60, 0.42, 0.98, 0.5
        BoxLayout:
            id: chat
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: 0, dp(8)
            spacing: dp(4)

    # ---- Input bar ----
    BoxLayout:
        size_hint_y: None
        height: dp(72)
        padding: dp(14), dp(12)
        spacing: dp(10)
        TextInput:
            id: inp
            hint_text: 'Message Aizen'
            multiline: False
            write_tab: False
            font_size: sp(15)
            background_normal: ''
            background_active: ''
            background_color: 0, 0, 0, 0
            foreground_color: 0.93, 0.91, 0.98, 1
            hint_text_color: 0.50, 0.45, 0.66, 1
            cursor_color: 0.60, 0.42, 0.98, 1
            padding: [dp(18), (self.height - self.line_height) / 2.0, dp(18), 0]
            on_text_validate: root.send()
            canvas.before:
                Color:
                    rgba: 0.121, 0.082, 0.204, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(24)]
        Pill:
            text: 'Mic'
            size_hint_x: None
            width: dp(56)
            on_release: root.on_mic()
        Pill:
            text: 'Send'
            bold: True
            size_hint_x: None
            width: dp(72)
            fill: 0.60, 0.42, 0.98, 1
            fill_down: 0.47, 0.32, 0.82, 1
            color: 1, 1, 1, 1
            on_release: root.send()
"""


class Root(BoxLayout):
    orb_h = NumericProperty(dp(210))
    status = StringProperty('Online')
    status_color = ListProperty(GREEN)
    busy = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = []
        self.compact = False
        self._typing = None

    # ---------- UI helpers ----------
    def greet(self, *args):
        self.add_bubble(
            "Welcome. I've been expecting you. What shall we work on today?",
            mine=False)

    def add_bubble(self, text, mine):
        b = Bubble(text=text, mine=mine)
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
            lambda dt: setattr(box, 'cursor', (len(prefix), 0)), 0.1)

    def set_state(self, busy, label=None, color=None):
        self.busy = busy
        self.ids.orb.thinking = busy
        if busy:
            self.status, self.status_color = 'Thinking', AMBER
        else:
            self.status = label or 'Online'
            self.status_color = color or GREEN

    def shrink_orb(self):
        if not self.compact:
            self.compact = True
            Animation(orb_h=dp(92), duration=0.35, t='out_cubic').start(self)

    # ---------- Actions ----------
    VOICE_CODE = 4242

    def on_mic(self):
        try:
            from android import activity
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            RI = autoclass('android.speech.RecognizerIntent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(RI.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RI.EXTRA_LANGUAGE_MODEL,
                            RI.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RI.EXTRA_LANGUAGE, "hi-IN")
            intent.putExtra(RI.EXTRA_PROMPT, "Speak to Aizen")
            activity.unbind(on_activity_result=self._on_voice_result)
            activity.bind(on_activity_result=self._on_voice_result)
            PythonActivity.mActivity.startActivityForResult(
                intent, self.VOICE_CODE)
        except Exception:
            self.add_bubble("Voice input works only on the Android app.",
                            mine=False)

    def _on_voice_result(self, request_code, result_code, intent):
        if request_code != self.VOICE_CODE or result_code != -1 or not intent:
            return
        try:
            from jnius import autoclass
            RI = autoclass('android.speech.RecognizerIntent')
            results = intent.getStringArrayListExtra(RI.EXTRA_RESULTS)
            text = str(results.get(0)) if results and results.size() else ''
        except Exception:
            text = ''
        if text:
            def _go(dt):
                self.ids.inp.text = text
                self.send()
            Clock.schedule_once(_go, 0)

    def send(self):
        box = self.ids.inp
        msg = box.text.strip()
        if not msg or self.busy:
            return
        box.text = ''
        self.shrink_orb()
        self.add_bubble(msg, mine=True)
        self._typing = self.add_bubble('Thinking...', mine=False)
        self.set_state(True)

        self.history.append({"role": "user", "content": msg})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += self.history[-12:]
        body = json.dumps({"model": MODEL, "messages": messages})
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Cloudflare error 1010 default Python User-Agent block karta hai
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AizenApp/1.0",
        }
        UrlRequest(
            WORKER_URL, req_body=body, req_headers=headers, timeout=60,
            ca_file=CA_FILE,
            on_success=self._on_success,
            on_failure=self._on_failure,
            on_error=self._on_error,
        )
        Clock.schedule_once(lambda dt: setattr(box, 'focus', True), 0.1)

    # ---------- Network callbacks ----------
    def _finish(self, text, ok=True):
        if self._typing is not None:
            self.ids.chat.remove_widget(self._typing)
            self._typing = None
        self.add_bubble(text, mine=False)
        if ok:
            self.history.append({"role": "assistant", "content": text})
            self.set_state(False)
        else:
            self.set_state(False, 'Error', RED)

    def _on_success(self, req, result):
        try:
            if isinstance(result, (bytes, str)):
                result = json.loads(result)
            text = result["choices"][0]["message"]["content"]
            text = text.replace("**", "").strip()
            self._finish(text or "I got an empty reply. Please try again.")
        except Exception:
            self._finish("The server sent a reply I couldn't read. "
                         "Check your Worker response format.", ok=False)

    def _on_failure(self, req, result):
        code = getattr(req, 'resp_status', '?')
        hint = ""
        if code == 403:
            hint = " The Worker or Cloudflare blocked the request."
        elif code in (401, 402):
            hint = " Check the OpenRouter API key and credits in the Worker."
        self._finish("Request failed (HTTP %s).%s" % (code, hint), ok=False)

    def _on_error(self, req, error):
        self._finish("No connection. Check your internet and try again.",
                     ok=False)


class AizenApp(App):
    title = 'Aizen'

    def build(self):
        Window.clearcolor = BG
        Window.softinput_mode = 'resize'
        Builder.load_string(KV)
        return Root()

    def on_start(self):
        Clock.schedule_once(self.root.greet, 0.2)


if __name__ == '__main__':
    AizenApp().run()
