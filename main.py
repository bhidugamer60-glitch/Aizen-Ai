
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window


class AizenApp(App):

    def build(self):
        self.title = "Aizen AI"

        root = BoxLayout(
            orientation="vertical",
            padding=12,
            spacing=10
        )

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

        scroll = ScrollView()
        scroll.add_widget(self.chat)
        root.add_widget(scroll)

        self.message = TextInput(
            hint_text="Message Aizen...",
            multiline=False,
            size_hint_y=None,
            height=55
        )
        root.add_widget(self.message)

        send_button = Button(
            text="Send",
            size_hint_y=None,
            height=50
        )
        send_button.bind(on_press=self.send_message)
        root.add_widget(send_button)

        return root

    def send_message(self, instance):
        message = self.message.text.strip()

        if not message:
            return

        self.chat.text += f"\n\nYou: {message}"
        self.chat.text += "\n\nAizen: AI connection coming soon!"

        self.message.text = ""


if __name__ == "__main__":
    AizenApp().run()
