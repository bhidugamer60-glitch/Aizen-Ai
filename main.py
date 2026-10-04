import json
import threading

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

try:
    import certifi
    CA_FILE = certifi.where()
except Exception:
    CA_FILE = None

# ---------------------------------------------------------------------------
# AIZEN CONFIG
# ---------------------------------------------------------------------------
WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev"
MODEL = "openai/gpt-4o-mini:online"

SYSTEM_PROMPT = (
    "You are Aizen, a personal AI assistant. Reply in the same language "
    "the user writes in. If the user writes Hinglish, reply in Hinglish. "
    "Be clear, friendly, useful and concise. You can use web search when "
    "the user's request needs current information. Do not use markdown "
    "formatting."
)

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

        import math

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
            Color(
                outer[0],
                outer[1],
                outer[2],
                0.08 + 0.05 * pulse,
            )
            Ellipse(
                pos=(cx - r, cy - r),
                size=(2 * r, 2 * r),
            )

            Color(
                outer[0],
                outer[1],
                outer[2],
                0.14 + 0.05 * pulse,
            )
            rr = r * (0.80 + 0.03 * pulse)
            Ellipse(
                pos=(cx - rr, cy - rr),
                size=(2 * rr, 2 * rr),
            )

            Color(0.06, 0.09, 0.18, 1)
            rr = r * 0.62
            Ellipse(
                pos=(cx - rr, cy - rr),
                size=(2 * rr, 2 * rr),
            )

            Color(
                outer[0],
                outer[1],
                outer[2],
                0.30,
            )
            Line(
                circle=(cx, cy, r * 0.70),
                width=dp(1.2),
            )

            Color(
                min(outer[0] + 0.20, 1),
                min(outer[1] + 0.20, 1),
                min(outer[2] + 0.20, 1),
                1,
            )
            Line(
                circle=(
                    cx,
                    cy,
                    r * 0.70,
                    self.angle,
                    self.angle + 85,
                ),
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

            Ellipse(
                pos=(cx - rc, cy - rc),
                size=(2 * rc, 2 * rc),
            )


class Bubble(BoxLayout):
    text = StringProperty("")
    mine = BooleanProperty(False)


KV = """
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<Pill>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 0.91, 0.93, 0.97, 1
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
                rgba: (0.30, 0.55, 1.0, 1) if root.mine else (0.11, 0.15, 0.28, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(18), dp(18), dp(4), dp(18)] if root.mine else [dp(18), dp(18), dp(18), dp(4)]

        Label:
            id: msg
            text: root.text
            font_size: sp(15)
            color: (1, 1, 1, 1) if root.mine else (0.91, 0.93, 0.97, 1)
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
            rgba: 0.043, 0.063, 0.125, 1
        Rectangle:
            pos: self.pos
            size: self.size

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
                color: 0.91, 0.93, 0.97, 1
                halign: 'left'
                valign: 'bottom'
                text_size: self.size

            Label:
                text: root.subtitle
                font_size: sp(12)
                color: 0.54, 0.58, 0.70, 1
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
                        rgba: 0.09, 0.13, 0.25, 1
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
                    color: 0.91, 0.93, 0.97, 1
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size

    FloatLayout:
        size_hint_y: None
        height: root.orb_h

        Orb:
            id: orb
            size_hint: None, None
            size: root.orb_h - dp(16), root.orb_h - dp(16)
            pos_hint: {'center_x': .5, 'center_y': .5}

        Label:
            text: root.orb_label
            size_hint: None, None
            size: dp(180), dp(28)
            pos_hint: {'center_x': .5, 'y': .03}
            color: 0.65, 0.72, 0.90, 1
            font_size: sp(12)
            halign: 'center'
            text_size: self.size

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

    ScrollView:
        id: scroll
        do_scroll_x: False
        bar_width: dp(3)
        bar_color: 0.30, 0.55, 1, 0.5

        BoxLayout:
            id: chat
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: 0, dp(8)
            spacing: dp(4)

    BoxLayout:
        size_hint_y: None
        height: dp(72)
        padding: dp(14), dp(12)
        spacing: dp(8)

        TextInput:
            id: inp
            hint_text: 'Message Aizen'
            multiline: False
            write_tab: False
            font_size: sp(15)
            background_normal: ''
            background_active: ''
            background_color: 0, 0, 0, 0
            foreground_color: 0.91, 0.93, 0.97, 1
            hint_text_color: 0.45, 0.50, 0.65, 1
            cursor_color: 0.30, 0.55, 1, 1
            padding: [dp(18), (self.height - self.line_height) / 2.0, dp(18), 0]
            on_text_validate: root.send()

            canvas.before:
                Color:
                    rgba: 0.09, 0.13, 0.25, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(24)]

        Pill:
            text: 'Call'
            size_hint_x: None
            width: dp(58)
            fill: 0.12, 0.34, 0.29, 1
            fill_down: 0.10, 0.27, 0.23, 1
            on_release: root.toggle_call()

        Pill:
            text: 'Send'
            bold: True
            size_hint_x: None
            width: dp(68)
            fill: 0.30, 0.55, 1, 1
            fill_down: 0.22, 0.43, 0.85, 1
            color: 1, 1, 1, 1
            on_release: root.send()
"""


class Root(BoxLayout):
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
        self._tts = None
        self._recognizer = None
        self._recognition_listener = None

    # -----------------------------------------------------------------------
    # Android voice setup
    # -----------------------------------------------------------------------
    def _setup_android_voice(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method

            self._PythonJavaClass = PythonJavaClass
            self._java_method = java_method
            self._autoclass = autoclass

            Context = autoclass("android.content.Context")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            activity = PythonActivity.mActivity

            self._activity = activity
            self._speech_manager = activity.getSystemService(
                Context.SPEECH_SERVICE
            )

            self._tts = autoclass(
                "android.speech.tts.TextToSpeech"
            )(
                activity,
                self._TTSListener(self)
            )

            self._recognizer = autoclass(
                "android.speech.SpeechRecognizer"
            ).createSpeechRecognizer(activity)

            self._recognition_listener = self._RecognitionListener(self)
            self._recognizer.setRecognitionListener(
                self._recognition_listener
            )

            return True

        except Exception:
            self._tts = None
            self._recognizer = None
            return False

    class _TTSListener:
        def __init__(self, root):
            self.root = root

        def onInit(self, status):
            try:
                self.root._tts_ready = True
            except Exception:
                pass

    class _RecognitionListener:
        def __init__(self, root):
            self.root = root

        def onReadyForSpeech(self, params):
            Clock.schedule_once(
                lambda dt: self.root._voice_state("listening"),
                0
            )

        def onBeginningOfSpeech(self):
            Clock.schedule_once(
                lambda dt: self.root._voice_state("listening"),
                0
            )

        def onRmsChanged(self, rmsdB):
            pass

        def onBufferReceived(self, buffer):
            pass

        def onEndOfSpeech(self):
            Clock.schedule_once(
                lambda dt: self.root._voice_state("thinking"),
                0
            )

        def onError(self, error):
            Clock.schedule_once(
                lambda dt: self.root._voice_error(),
                0
            )

        def onResults(self, results):
            try:
                matches = results.getStringArrayList(
                    "results_recognition"
                )

                if matches and matches.size() > 0:
                    text = str(matches.get(0))
                    Clock.schedule_once(
                        lambda dt: self.root._voice_result(text),
                        0
                    )
                else:
                    Clock.schedule_once(
                        lambda dt: self.root._voice_error(),
                        0
                    )
            except Exception:
                Clock.schedule_once(
                    lambda dt: self.root._voice_error(),
                    0
                )

        def onPartialResults(self, results):
            pass

        def onEvent(self, eventType, params):
            pass

    # -----------------------------------------------------------------------
    # UI helpers
    # -----------------------------------------------------------------------
    def greet(self, *args):
        self.add_bubble(
            "Hi, I'm Aizen. Tap Call for voice conversation, "
            "or send me a message.",
            mine=False
        )

    def add_bubble(self, text, mine):
        b = Bubble(
            text=str(text),
            mine=mine
        )
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
            lambda dt: setattr(
                box,
                "cursor",
                (len(prefix), 0)
            ),
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

            Animation(
                orb_h=dp(112),
                duration=0.35,
                t="out_cubic"
            ).start(self)

    # -----------------------------------------------------------------------
    # Voice state
    # -----------------------------------------------------------------------
    def _voice_state(self, state):
        if state == "listening":
            self.ids.orb.listening = True
            self.ids.orb.thinking = False
            self.ids.orb.speaking = False
            self.status = "Listening"
            self.status_color = GREEN
            self.orb_label = "I'm listening..."

        elif state == "thinking":
            self.ids.orb.listening = False
            self.ids.orb.thinking = True
            self.ids.orb.speaking = False
            self.status = "Thinking"
            self.status_color = AMBER
            self.orb_label = "Aizen is thinking..."

        elif state == "speaking":
            self.ids.orb.listening = False
            self.ids.orb.thinking = False
            self.ids.orb.speaking = True
            self.status = "Speaking"
            self.status_color = ACCENT
            self.orb_label = "Aizen is speaking..."

        else:
            self.ids.orb.listening = False
            self.ids.orb.thinking = False
            self.ids.orb.speaking = False
            self.status = "Online"
            self.status_color = GREEN
            self.orb_label = "Aizen AI"

    def _voice_error(self):
        self._voice_state("idle")

        if self.call_active:
            self.add_bubble(
                "I couldn't hear that. Tap Call again and speak clearly.",
                mine=False
            )

    def _voice_result(self, text):
        text = str(text).strip()

        if not text:
            self._voice_error()
            return

        self.ids.inp.text = text

        if self.call_active:
            self.send()

    # -----------------------------------------------------------------------
    # Call
    # -----------------------------------------------------------------------
    def toggle_call(self):
        if self.call_active:
            self.end_call()
        else:
            self.start_call()

    def start_call(self):
        if self.busy:
            return

        if self._recognizer is None or self._tts is None:
            if not self._setup_android_voice():
                self.add_bubble(
                    "Voice isn't available in this build. "
                    "Make sure RECORD_AUDIO permission is enabled.",
                    mine=False
                )
                return

        self.call_active = True
        self.subtitle = "Voice call active"
        self.orb_h = dp(210)

        try:
            self._request_mic_permission()
        except Exception:
            pass

        Clock.schedule_once(
            lambda dt: self._start_listening(),
            0.5
        )

    def end_call(self):
        self.call_active = False
        self.subtitle = "Personal assistant"

        try:
            if self._recognizer is not None:
                self._recognizer.cancel()
        except Exception:
            pass

        try:
            if self._tts is not None:
                self._tts.stop()
        except Exception:
            pass

        self._voice_state("idle")

    def _request_mic_permission(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions(
                [Permission.RECORD_AUDIO]
            )
        except Exception:
            pass

    def _start_listening(self):
        if not self.call_active or self._recognizer is None:
            return

        try:
            Intent = self._autoclass("android.content.Intent")
            RecognizerIntent = self._autoclass(
                "android.speech.RecognizerIntent"
            )

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                False
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_MAX_RESULTS,
                1
            )

            self._recognizer.startListening(intent)

        except Exception as exc:
            self._voice_error()

    # -----------------------------------------------------------------------
    # Text-to-speech
    # -----------------------------------------------------------------------
    def speak(self, text):
        if self._tts is None:
            return

        clean = str(text).strip()

        if not clean:
            return

        def do_speak():
            try:
                self._voice_state("speaking")

                # Android TTS queue constants
                QUEUE_FLUSH = 0

                self._tts.speak(
                    clean,
                    QUEUE_FLUSH,
                    None
                )

                # Return to listening after a safe delay.
                delay = max(
                    1.5,
                    min(12.0, len(clean) * 0.065)
                )

                Clock.schedule_once(
                    lambda dt: self._after_speak(),
                    delay
                )

            except Exception:
                Clock.schedule_once(
                    lambda dt: self._after_speak(),
                    0
                )

        Clock.schedule_once(
            lambda dt: do_speak(),
            0
        )

    def _after_speak(self):
        if self.call_active:
            self._voice_state("idle")
            Clock.schedule_once(
                lambda dt: self._start_listening(),
                0.35
            )
        else:
            self._voice_state("idle")

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------
    def on_mic(self):
        self.start_call()

    def send(self):
        box = self.ids.inp
        msg = box.text.strip()

        if not msg or self.busy:
            return

        box.text = ""
        self.shrink_orb()

        self.add_bubble(
            msg,
            mine=True
        )

        self._typing = self.add_bubble(
            "Thinking...",
            mine=False
        )

        self.set_state(True)

        self.history.append({
            "role": "user",
            "content": msg
        })

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        messages += self.history[-12:]

        body = json.dumps({
            "model": MODEL,
            "messages": messages
        })

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 13) AizenApp/1.0"
            ),
        }

        UrlRequest(
            WORKER_URL,
            req_body=body,
            req_headers=headers,
            timeout=60,
            ca_file=CA_FILE,
            on_success=self._on_success,
            on_failure=self._on_failure,
            on_error=self._on_error,
        )

        Clock.schedule_once(
            lambda dt: setattr(box, "focus", True),
            0.1
        )

    # -----------------------------------------------------------------------
    # Network callbacks
    # -----------------------------------------------------------------------
    def _finish(self, text, ok=True):
        if self._typing is not None:
            try:
                self.ids.chat.remove_widget(self._typing)
            except Exception:
                pass

            self._typing = None

        self.add_bubble(
            text,
            mine=False
        )

        if ok:
            self.history.append({
                "role": "assistant",
                "content": text
            })
            self.set_state(False)

            if self.call_active:
                self.speak(text)
        else:
            self.set_state(
                False,
                "Error",
                RED
            )

            if self.call_active:
                self._voice_state("idle")

    def _on_success(self, req, result):
        try:
            if isinstance(result, (bytes, str)):
                result = json.loads(result)

            text = result["choices"][0]["message"]["content"]
            text = str(text).replace("**", "").strip()

            self._finish(
                text or "I got an empty reply. Please try again."
            )

        except Exception:
            self._finish(
                "The server sent a reply I couldn't read. "
                "Check your Worker response format.",
                ok=False
            )

    def _on_failure(self, req, result):
        code = getattr(
            req,
            "resp_status",
            "?"
        )

        hint = ""

        if code == 403:
            hint = " The Worker or Cloudflare blocked the request."

        elif code in (401, 402):
            hint = (
                " Check the OpenRouter API key and credits "
                "in the Worker."
            )

        self._finish(
            "Request failed (HTTP %s).%s" % (code, hint),
            ok=False
        )

    def _on_error(self, req, error):
        self._finish(
            "No connection. Check your internet and try again.",
            ok=False
        )


class AizenApp(App):
    title = "Aizen"

    def build(self):
        Window.clearcolor = BG
        Window.softinput_mode = "resize"
        Builder.load_string(KV)
        return Root()

    def on_start(self):
        Clock.schedule_once(
            self._initialize_voice,
            0.8
        )
        Clock.schedule_once(
            self.root.greet,
            0.3
        )

    def _initialize_voice(self, *args):
        try:
            self.root._setup_android_voice()
        except Exception:
            pass

    def on_stop(self):
        try:
            if self.root._recognizer is not None:
                self.root._recognizer.destroy()
        except Exception:
            pass

        try:
            if self.root._tts is not None:
                self.root._tts.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    AizenApp().run()
