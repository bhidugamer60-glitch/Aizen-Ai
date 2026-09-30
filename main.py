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


# ==============================
# AIZEN CONFIG
# ==============================

OPENROUTER_API_KEY = ""

MODEL = "openai/gpt-4o-mini"

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ==============================
# AIZEN APP
# ==============================

class AizenApp(App):

    def build(self):
        self.title = "Aizen AI"

        # Conversation memory for current app session
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
        # SEND BUTTON
        # ==============================

        self.send_button = Button(
            text="Send",
            size_hint_y=None,
            height=50
        )

        self.send_button.bind(
            on_press=self.send_message
        )

        root.add_widget(self.send_button)

        return root

    # ==============================
    # SEND MESSAGE
    # ==============================

    def send_message(self, instance):
        message = self.message.text.strip()

        if not message:
            return

        self.message.text = ""

        # Show user message
        self.chat.text += f"\n\nYou: {message}"

        # Add to conversation memory
        self.messages.append({
            "role": "user",
            "content": message
        })

        # Disable button while AI is thinking
        self.send_button.disabled = True
        self.send_button.text = "Aizen is thinking..."

        # Run API in background
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
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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

            # Save AI response to conversation
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
            except:
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

        self.chat.text += f"\n\nAizen: {reply}"

        self.send_button.disabled = False
        self.send_button.text = "Send"

        self.scroll_to_bottom()

    # ==============================
    # SHOW ERROR
    # ==============================

    def show_error(self, error):

        self.chat.text += (
            f"\n\nAizen: Sorry bhai, connection problem.\n"
            f"{error}"
        )

        self.send_button.disabled = False
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


if __name__ == "__main__":
    AizenApp().run()

Abhi sirf 2 kaam kar:

1. "main.py" ka pura purana code delete karke upar wala code paste kar.
2. "PASTE_YOUR_OPENROUTER_API_KEY_HERE" ko apni existing OpenRouter API key se replace kar.

Buildozer.spec ko bilkul mat badalna. Uska working configuration same rahega.

Is version mein Aizen actual OpenRouter se reply karega aur current conversation ko yaad rakhega. Uske baad hum next step mein voice input/output + "bankai" activation + "hell" deactivation add karenge.
