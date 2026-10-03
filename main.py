from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.metrics import dp
from threading import Thread
import json
import urllib.request
import urllib.error
import ssl
import math

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CONTEXT = ssl.create_default_context()

try:
    from jnius import autoclass
    from android import activity
    from android.permissions import request_permissions, Permission
    Intent = autoclass("android.content.Intent")
    RecognizerIntent = autoclass("android.speech.RecognizerIntent")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    ANDROID = True
except Exception:
    ANDROID = False

WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev"
APP_TOKEN = ""
MODEL = "openai/gpt-4o-mini"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)
VOICE_REQUEST_CODE = 1001
RESULT_OK = -1

BG = (0.025, 0.03, 0.045, 1)
CARD = (0.055, 0.065, 0.09, 1)
CARD2 = (0.075, 0.085, 0.12, 1)
BLUE = (0.20, 0.55, 1.0, 1)
BLUE_SOFT = (0.20, 0.45, 0.85, 1)
WHITE = (0.92, 0.95, 1, 1)
TEXT = (0.72, 0.77, 0.86, 1)
MUTED = (0.42, 0.48, 0.58, 1)


class AizenCore(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.t = 0
        with self.canvas:
            Color(0.10, 0.35, 0.90, 0.10)
            self.glow3 = Ellipse()
            Color(0.12, 0.42, 1.0, 0.16)
            self.glow2 = Ellipse()
            Color(0.15, 0.52, 1.0, 0.30)
            self.glow1 = Ellipse()
            Color(0.05, 0.08, 0.14, 1)
            self.core = Ellipse()
            Color(0.20, 0.60, 1.0, 0.9)
            self.ring = Line(circle=(0, 0, 50, 0), width=1.4)
            Color(0.55, 0.80, 1.0, 0.9)
            self.inner = Ellipse()
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        Clock.schedule_interval(self.animate, 1 / 30)

    def update_graphics(self, *args):
        cx, cy = self.center_x, self.center_y
        base = min(self.width, self.height)
        if base <= 0:
            return
        r = base * 0.28
        self.core.pos = (cx - r, cy - r)
        self.core.size = (r * 2, r * 2)
        self.glow1.pos = (cx - r * 1.45, cy - r * 1.45)
        self.glow1.size = (r * 2.9, r * 2.9)
        self.glow2.pos = (cx - r * 1.85, cy - r * 1.85)
        self.glow2.size = (r * 3.7, r * 3.7)
        self.glow3.pos = (cx - r * 2.3, cy - r * 2.3)
        self.glow3.size = (r * 4.6, r * 4.6)
        ir = r * 0.22
        self.inner.pos = (cx - ir, cy - ir)
        self.inner.size = (ir * 2, ir * 2)
        self.ring.circle = (cx, cy, r * 1.35, self.t * 45)

    def animate(self, dt):
        self.t += dt
        pulse = 1 + math.sin(self.t * 2.2) * 0.035
        cx, cy = self.center_x, self.center_y
        base = min(self.width, self.height)
        if base <= 0:
            return
        r = base * 0.28 * pulse
        self.core.pos = (cx - r, cy - r)
        self.core.size = (r * 2, r * 2)
        self.glow1.pos = (cx - r * 1.45, cy - r * 1.45)
        self.glow1.size = (r * 2.9, r * 2.9)
        self.glow2.pos = (cx - r * 1.85, cy - r * 1.85)
        self.glow2.size = (r * 3.7, r * 3.7)
        self.glow3.pos = (cx - r * 2.3, cy - r * 2.3)
        self.glow3.size = (r * 4.6, r * 4.6)
        self.ring.circle = (cx, cy, r * 1.35, self.t * 45)


class AizenApp(App):
    def build(self):
        self.title = "Aizen AI"
        self.messages = [{
            "role": "system",
            "content": (
                "You are Aizen, a friendly personal AI assistant. "
                "Reply in Hinglish or English, matching the user's language. "
                "Talk casually like a helpful best friend and use 'bhai' "
                "naturally when appropriate. Be helpful, concise and clear."
            )
        }]

        if ANDROID:
            try:
                request_permissions([Permission.RECORD_AUDIO])
            except Exception:
                pass

        root = FloatLayout()
        with root.canvas.before:
            Color(*BG)
            self.background = RoundedRectangle(pos=root.pos, size=root.size, radius=[0])
        root.bind(
            pos=lambda obj, val: setattr(self.background, "pos", val),
            size=lambda obj, val: setattr(self.background, "size", val)
        )

        main = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(18), dp(20), dp(12)],
            spacing=dp(10)
        )
        root.add_widget(main)

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58))
        title_box = BoxLayout(orientation="vertical", spacing=0)
        title_box.add_widget(Label(
            text="[b]A I Z E N[/b]", markup=True, font_size="24sp",
            color=WHITE, halign="left"
        ))
        title_box.add_widget(Label(
            text="PERSONAL INTELLIGENCE", font_size="9sp", color=MUTED, halign="left"
        ))
        header.add_widget(title_box)
        header.add_widget(Button(
            text="⚙", font_size="22sp", color=TEXT,
            background_normal="", background_color=(0, 0, 0, 0),
            size_hint_x=None, width=dp(50)
        ))
        main.add_widget(header)

        main.add_widget(Label(
            text="●  SYSTEM ONLINE", font_size="11sp", color=BLUE,
            size_hint_y=None, height=dp(25)
        ))

        core_area = FloatLayout(size_hint_y=0.95)
        self.core = AizenCore(size_hint=(None, None), size=(dp(230), dp(230)))
        core_area.add_widget(self.core)

        def position_core(instance, value):
            self.core.center = (core_area.center_x, core_area.center_y + dp(5))
        core_area.bind(size=position_core, pos=position_core)

        core_name = Label(
            text="[b]AIZEN[/b]", markup=True, font_size="20sp", color=WHITE,
            size_hint=(None, None), size=(dp(200), dp(35)),
            pos_hint={"center_x": 0.5, "y": 0.02}
        )
        core_area.add_widget(core_name)
        main.add_widget(core_area)

        main.add_widget(Label(
            text="AI CORE  •  READY", font_size="10sp", color=MUTED,
            size_hint_y=None, height=dp(25)
        ))

        self.start_button = Button(
            text="🎙   START CONVERSATION", font_size="15sp", bold=True,
            color=WHITE, background_normal="", background_color=BLUE,
            size_hint_y=None, height=dp(58)
        )
        self.start_button.bind(on_press=self.start_voice_input)
        main.add_widget(self.start_button)

        modules = BoxLayout(
            orientation="horizontal", spacing=dp(10),
            size_hint_y=None, height=dp(58)
        )
        for label in ("🧠\nCORE", "✦\nEDITOR", "◇\nTOOLS", "∞\nMEMORY"):
            modules.add_widget(Button(
                text=label, font_size="10sp", color=TEXT,
                background_normal="", background_color=CARD,
                halign="center", valign="middle"
            ))
        main.add_widget(modules)

        message_area = BoxLayout(
            orientation="horizontal", spacing=dp(7),
            size_hint_y=None, height=dp(52)
        )
        self.message = TextInput(
            hint_text="Message Aizen...", multiline=False, font_size="14sp",
            foreground_color=WHITE, hint_text_color=MUTED,
            background_normal="", background_active="",
            background_color=CARD2, padding=[dp(15), dp(15)]
        )
        self.message.bind(on_text_validate=self.send_message)
        message_area.add_widget(self.message)

        self.mic_button = Button(
            text="🎙", font_size="20sp", color=WHITE,
            background_normal="", background_color=BLUE_SOFT,
            size_hint_x=None, width=dp(52)
        )
        self.mic_button.bind(on_press=self.start_voice_input)
        message_area.add_widget(self.mic_button)

        self.send_button = Button(
            text="➤", font_size="22sp", color=WHITE,
            background_normal="", background_color=BLUE,
            size_hint_x=None, width=dp(52)
        )
        self.send_button.bind(on_press=self.send_message)
        message_area.add_widget(self.send_button)
        main.add_widget(message_area)

        self.chat = Label(
            text="Aizen AI Ready!\n\nHey bhai! Welcome back.",
            font_size="16sp", color=TEXT, halign="left", valign="top",
            size_hint_y=None
        )
        self.chat.bind(
            width=lambda instance, value: setattr(instance, "text_size", (value, None))
        )
        self.chat.bind(
            texture_size=lambda instance, value: setattr(instance, "height", value[1] + dp(30))
        )
        self.scroll = ScrollView(size_hint_y=None, height=0, opacity=0)
        self.scroll.add_widget(self.chat)
        main.add_widget(self.scroll, index=1)

        if ANDROID:
            try:
                activity.bind(on_activity_result=self.on_activity_result)
            except Exception:
                pass
        return root

    def start_voice_input(self, instance):
        if not ANDROID:
            self.chat.text += "\n\nAizen: Voice input Android APK me available hoga."
            self.scroll_to_bottom()
            return
        try:
            self.mic_button.text = "..."
            self.start_button.text = "●   LISTENING..."
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN")
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to Aizen")
            PythonActivity.mActivity.startActivityForResult(intent, VOICE_REQUEST_CODE)
        except Exception as e:
            self.mic_button.text = "🎙"
            self.start_button.text = "🎙   START CONVERSATION"
            self.chat.text += "\n\nAizen: Mic start nahi ho paya.\n" + str(e)
            self.scroll_to_bottom()

    def on_activity_result(self, request_code, result_code, intent):
        if request_code != VOICE_REQUEST_CODE:
            return
        spoken_text = None
        error = None
        try:
            if result_code == RESULT_OK and intent is not None:
                results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if results is not None and results.size() > 0:
                    spoken_text = str(results.get(0))
        except Exception as e:
            error = str(e)
        Clock.schedule_once(lambda dt: self.handle_voice_result(spoken_text, error))

    def handle_voice_result(self, spoken_text, error):
        self.mic_button.text = "🎙"
        self.start_button.text = "🎙   START CONVERSATION"
        if error:
            self.chat.text += "\n\nAizen: Voice result read nahi ho paya.\n" + error
            self.scroll_to_bottom()
            return
        if spoken_text:
            self.message.text = spoken_text
            self.send_message(None)

    def send_message(self, instance):
        message = self.message.text.strip()
        if not message or self.send_button.disabled:
            return
        self.message.text = ""
        self.chat.text += f"\n\nYou: {message}"
        self.messages.append({"role": "user", "content": message})
        self.send_button.disabled = True
        self.mic_button.disabled = True
        self.start_button.disabled = True
        self.send_button.text = "..."
        Thread(target=self.ask_aizen, daemon=True).start()
        self.scroll_to_bottom()

    def ask_aizen(self):
        try:
            data = {
                "model": MODEL,
                "messages": self.messages,
                "temperature": 0.7
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": USER_AGENT
            }
            if APP_TOKEN:
                headers["X-App-Token"] = APP_TOKEN
            request = urllib.request.Request(
                WORKER_URL,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(
                request, timeout=60, context=SSL_CONTEXT
            ) as response:
                result = json.loads(response.read().decode("utf-8"))
            reply = result["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": reply})
            Clock.schedule_once(lambda dt: self.show_reply(reply))
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                error_body = ""
            error_message = f"HTTP Error {e.code}\n{error_body}"
            Clock.schedule_once(lambda dt: self.show_error(error_message))
        except urllib.error.URLError as e:
            error_message = (
                "Internet connection problem. Check your internet and try again.\n"
                f"{e.reason}"
            )
            Clock.schedule_once(lambda dt: self.show_error(error_message))
        except Exception as e:
            error_message = f"Something went wrong:\n{str(e)}"
            Clock.schedule_once(lambda dt: self.show_error(error_message))

    def show_reply(self, reply):
        self.chat.text += f"\n\nAizen: {reply}"
        self.send_button.disabled = False
        self.mic_button.disabled = False
        self.start_button.disabled = False
        self.send_button.text = "➤"
        self.scroll_to_bottom()

    def show_error(self, error):
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages.pop()
        self.chat.text += f"\n\nAizen: Sorry bhai, connection problem.\n{error}"
        self.send_button.disabled = False
        self.mic_button.disabled = False
        self.start_button.disabled = False
        self.send_button.text = "➤"
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        self.scroll.height = dp(220)
        self.scroll.opacity = 1
        Clock.schedule_once(
            lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1
        )


if __name__ == "__main__":
    AizenApp().run()
    
