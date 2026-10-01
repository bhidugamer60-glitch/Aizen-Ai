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
import os

# Android imports
try:
    from android import activity
    from android.permissions import request_permissions, Permission
    from android.content import Intent
    from android.speech import RecognizerIntent
    ANDROID = True
except ImportError:
    ANDROID = False


# ==============================
# AIZEN CONFIG
# ==============================

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

MODEL = "openai/gpt-4o-mini"

API_URL = "https://openrouter.ai/api/v1/chat/completions"


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

        # ==============================
        # REQUEST MIC PERMISSION
        # ==============================

        if ANDROID:
            try:
                request_permissions([
                    Permission.RECORD_AUDIO
                ])
            except Exception:
                pass

        # ==============================
        # ROOT
        # ==============================

        root = BoxLayout(
            orientation="vertical",
            padding=12,
            spacing=10
        )

        # ==============================
        # TITLE
        # ==============================

        title = Label(
            text="[b]AIZEN AI[/b]",
            markup=True,
            font_size="28sp",
            size_hint_y=None,
            height=60
        )

        root.add_widget(title)

        # ==============================
        # CHAT AREA
        # ==============================

        self.chat = Label(
            text="Aizen AI Ready!\n\nHey bhai! Welcome back.",
            font_size="17sp",
            halign="left",
            valign="top",
            size_hint_y=None
        )

        self.chat.bind(
            width=lambda instance, value: setattr(
                instance,
                "text_size",
                (value, None)
            )
        )

        self.chat.bind(
            texture_size=lambda instance, value: setattr(
                instance,
                "height",
                value[1] + 30
            )
        )

        self.scroll = ScrollView()
        self.scroll.add_widget(self.chat)

        root.add_widget(self.scroll)

        # ==============================
        # MESSAGE INPUT
        # ==============================

        self.message = TextInput(
            hint_text="Message Aizen...",
            multiline=False,
            size_hint_y=None,
            height=55
        )

        self.message.bind(
            on_text_validate=self.send_message
        )

        root.add_widget(self.message)

        # ==============================
        # BUTTON ROW
        # ==============================

        button_row = BoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint_y=None,
            height=55
        )

        # MIC BUTTON

        self.mic_button = Button(
            text="🎤 Mic",
            size_hint_x=0.35
        )

        self.mic_button.bind(
            on_press=self.start_voice_input
        )

        button_row.add_widget(self.mic_button)

        # SEND BUTTON

        self.send_button = Button(
            text="Send",
            size_hint_x=0.65
        )

        self.send_button.bind(
            on_press=self.send_message
        )

        button_row.add_widget(self.send_button)

        root.add_widget(button_row)

        # Android activity result callback

        if ANDROID:
            try:
                activity.bind(
                    on_activity_result=self.on_activity_result
                )
            except Exception:
                pass

        return root

    # ==============================
    # VOICE INPUT
    # ==============================

    def start_voice_input(self, instance):

        if not ANDROID:
            self.chat.text += "\n\nAizen: Voice input Android APK me available hoga."
            return

        try:
            self.mic_button.text = "🎤 Listening..."

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "en-IN"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT,
                "Speak to Aizen"
            )

            activity.startActivityForResult(
                intent,
                1001
            )

        except Exception as e:

            self.mic_button.text = "🎤 Mic"

            self.chat.text += (
                "\n\nAizen: Mic start nahi ho paya.\n"
                + str(e)
            )

            self.scroll_to_bottom()

    # ==============================
    # VOICE RESULT
    # ==============================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != 1001:
            return

        self.mic_button.text = "🎤 Mic"

        try:

            if intent is None:
                return

            results = intent.getStringArrayListExtra(
                RecognizerIntent.EXTRA_RESULTS
            )

            if results and len(results) > 0:

                spoken_text = str(results[0])

                self.message.text = spoken_text

                # Automatically send voice message
                self.send_message(None)

        except Exception as e:

            self.chat.text += (
                "\n\nAizen: Voice result read nahi ho paya.\n"
                + str(e)
            )

            self.scroll_to_bottom()

    # ==============================
    # SEND MESSAGE
    # ==============================

    def send_message(self, instance):

        message = self.message.text.strip()

        if not message:
            return

        self.message.text = ""

        self.chat.text += (
            f"\n\nYou: {message}"
        )

        self.messages.append({
            "role": "user",
            "content": message
        })

        self.send_button.disabled = True
        self.mic_button.disabled = True

        self.send_button.text = "Aizen is thinking..."

        Thread(
            target=self.ask_aizen,
            args=(message,),
            daemon=True
        ).start()

        self.scroll_to_bottom()

    # ==============================
    # OPENROUTER REQUEST
    # ==============================

    def ask_aizen(self, message):

        try:

            if not OPENROUTER_API_KEY:

                Clock.schedule_once(
                    lambda dt: self.show_error(
                        "OpenRouter API key is not configured."
                    )
                )

                return

            data = {
                "model": MODEL,
                "messages": self.messages,
                "temperature": 0.7
            }

            request = urllib.request.Request(
                API_URL,
                data=json.dumps(data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": (
                        f"Bearer {OPENROUTER_API_KEY}"
                    ),
                    "HTTP-Referer": "https://github.com/",
                    "X-Title": "Aizen AI"
                },
                method="POST"
            )

            with urllib.request.urlopen(
                request,
                timeout=60
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

            reply = result["choices"][0]["message"]["content"]

            self.messages.append({
                "role": "assistant",
                "content": reply
            })

            Clock.schedule_once(
                lambda dt: self.show_reply(reply)
            )

        except urllib.error.HTTPError as e:

            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                error_body = ""

            error_message = (
                f"HTTP Error {e.code}\n"
                f"{error_body}"
            )

            Clock.schedule_once(
                lambda dt: self.show_error(error_message)
            )

        except urllib.error.URLError:

            Clock.schedule_once(
                lambda dt: self.show_error(
                    "Internet connection problem. "
                    "Check your internet and try again."
                )
            )

        except Exception as e:

            Clock.schedule_once(
                lambda dt: self.show_error(
                    f"Something went wrong:\n{str(e)}"
                )
            )

    # ==============================
    # SHOW AI REPLY
    # ==============================

    def show_reply(self, reply):

        self.chat.text += (
            f"\n\nAizen: {reply}"
        )

        self.send_button.disabled = False
        self.mic_button.disabled = False

        self.send_button.text = "Send"

        self.scroll_to_bottom()

    # ==============================
    # SHOW ERROR
    # ==============================

    def show_error(self, error):

        self.chat.text += (
            "\n\nAizen: Sorry bhai, connection problem.\n"
            f"{error}"
        )

        self.send_button.disabled = False
        self.mic_button.disabled = False

        self.send_button.text = "Send"

        self.scroll_to_bottom()

    # ==============================
    # SCROLL CHAT DOWN
    # ==============================

    def scroll_to_bottom(self):

        Clock.schedule_once(
            lambda dt: setattr(
                self.scroll,
                "scroll_y",
                0
            ),
            0.1
        )


# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    AizenApp().run()
