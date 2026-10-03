from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from threading import Thread
import json
import urllib.request
import urllib.error
import ssl

# Android par system certificates nahi milte, isliye certifi use karte hain
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CONTEXT = ssl.create_default_context()

# Android imports (pyjnius se, python-for-android me yehi sahi tarika hai)
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


# ==============================
# AIZEN CONFIG
# ==============================

WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev"

# Worker me APP_TOKEN secret set kiya ho to wahi yahan daalo, warna "" rehne do
APP_TOKEN = ""

MODEL = "openai/gpt-4o-mini"

# Cloudflare 1010 fix: normal browser jaisa User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)

VOICE_REQUEST_CODE = 1001
RESULT_OK = -1


# ==============================
# AIZEN APP
# ==============================

class AizenApp(App):

    def build(self):
        self.title = "Aizen AI"

        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are Aizen, a friendly personal AI assistant. "
                    "Reply in Hinglish or English, matching the user's language. "
                    "Talk casually like a helpful best friend and use 'bhai' "
                    "naturally when appropriate. Be helpful, concise and clear."
                )
            }
        ]

        if ANDROID:
            try:
                request_permissions([Permission.RECORD_AUDIO])
            except Exception:
                pass

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        title = Label(
            text="[b]AIZEN AI[/b]",
            markup=True,
            font_size="28sp",
            size_hint_y=None,
            height=60
        )
        root.add_widget(title)

        self.chat = Label(
            text="Aizen AI Ready!\n\nHey bhai! Welcome back.",
            font_size="17sp",
            halign="left",
            valign="top",
            size_hint_y=None
        )
        self.chat.bind(
            width=lambda instance, value: setattr(
                instance, "text_size", (value, None)
            )
        )
        self.chat.bind(
            texture_size=lambda instance, value: setattr(
                instance, "height", value[1] + 30
            )
        )

        self.scroll = ScrollView()
        self.scroll.add_widget(self.chat)
        root.add_widget(self.scroll)

        self.message = TextInput(
            hint_text="Message Aizen...",
            multiline=False,
            size_hint_y=None,
            height=55
        )
        self.message.bind(on_text_validate=self.send_message)
        root.add_widget(self.message)

        button_row = BoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint_y=None,
            height=55
        )

        self.mic_button = Button(text="Mic", size_hint_x=0.35)
        self.mic_button.bind(on_press=self.start_voice_input)
        button_row.add_widget(self.mic_button)

        self.send_button = Button(text="Send", size_hint_x=0.65)
        self.send_button.bind(on_press=self.send_message)
        button_row.add_widget(self.send_button)

        root.add_widget(button_row)

        if ANDROID:
            try:
                activity.bind(on_activity_result=self.on_activity_result)
            except Exception:
                pass

        return root

    # ==============================
    # VOICE INPUT
    # ==============================

    def start_voice_input(self, instance):

        if not ANDROID:
            self.chat.text += "\n\nAizen: Voice input Android APK me available hoga."
            self.scroll_to_bottom()
            return

        try:
            self.mic_button.text = "Listening..."

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN")
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to Aizen")

            PythonActivity.mActivity.startActivityForResult(
                intent, VOICE_REQUEST_CODE
            )

        except Exception as e:
            self.mic_button.text = "Mic"
            self.chat.text += "\n\nAizen: Mic start nahi ho paya.\n" + str(e)
            self.scroll_to_bottom()

    def on_activity_result(self, request_code, result_code, intent):
        # Ye function Android thread par chalta hai, Kivy thread par nahi.
        # Isliye yahan UI ko haath mat lagao, sirf data nikalo.

        if request_code != VOICE_REQUEST_CODE:
            return

        spoken_text = None
        error = None

        try:
            if result_code == RESULT_OK and intent is not None:
                results = intent.getStringArrayListExtra(
                    RecognizerIntent.EXTRA_RESULTS
                )
                if results is not None and results.size() > 0:
                    spoken_text = str(results.get(0))
        except Exception as e:
            error = str(e)

        # UI ka kaam Kivy ke main thread par bhejo
        Clock.schedule_once(
            lambda dt: self.handle_voice_result(spoken_text, error)
        )

    def handle_voice_result(self, spoken_text, error):

        self.mic_button.text = "Mic"

        if error:
            self.chat.text += (
                "\n\nAizen: Voice result read nahi ho paya.\n" + error
            )
            self.scroll_to_bottom()
            return

        if spoken_text:
            self.message.text = spoken_text
            self.send_message(None)

    # ==============================
    # SEND MESSAGE
    # ==============================

    def send_message(self, instance):

        message = self.message.text.strip()

        if not message:
            return

        # Ek saath do request na jaye
        if self.send_button.disabled:
            return

        self.message.text = ""
        self.chat.text += f"\n\nYou: {message}"

        self.messages.append({"role": "user", "content": message})

        self.send_button.disabled = True
        self.mic_button.disabled = True
        self.send_button.text = "Aizen is thinking..."

        Thread(target=self.ask_aizen, daemon=True).start()

        self.scroll_to_bottom()

    # ==============================
    # WORKER REQUEST
    # ==============================

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
                "User-Agent": USER_AGENT,
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
                "Internet connection problem. "
                f"Check your internet and try again.\n{e.reason}"
            )
            Clock.schedule_once(lambda dt: self.show_error(error_message))

        except Exception as e:

            error_message = f"Something went wrong:\n{str(e)}"
            Clock.schedule_once(lambda dt: self.show_error(error_message))

    # ==============================
    # SHOW REPLY / ERROR
    # ==============================

    def show_reply(self, reply):

        self.chat.text += f"\n\nAizen: {reply}"

        self.send_button.disabled = False
        self.mic_button.disabled = False
        self.send_button.text = "Send"

        self.scroll_to_bottom()

    def show_error(self, error):

        # Fail hui user message history se hata do, taaki next try saaf ho
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages.pop()

        self.chat.text += f"\n\nAizen: Sorry bhai, connection problem.\n{error}"

        self.send_button.disabled = False
        self.mic_button.disabled = False
        self.send_button.text = "Send"

        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        Clock.schedule_once(
            lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1
        )


if __name__ == "__main__":
    AizenApp().run()
