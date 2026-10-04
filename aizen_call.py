# aizen_call.py  -  PART 2c: call button logic and voice state (orb/status)
from kivy.utils import platform

from aizen_ui import ACCENT, AMBER, GREEN

if platform == "android":
    from android.permissions import request_permissions, check_permission, Permission


class CallMixin:
    """Start/stop a voice call and update the orb. Used by VoiceMixin."""

    def _voice_state(self, state):
        orb = self.ids.orb

        if state == "listening":
            orb.listening = True
            orb.thinking = False
            orb.speaking = False
            self.status = "Listening"
            self.status_color = GREEN
            self.orb_label = "I'm listening..."

        elif state == "thinking":
            orb.listening = False
            orb.thinking = True
            orb.speaking = False
            self.status = "Thinking"
            self.status_color = AMBER
            self.orb_label = "Aizen is thinking..."

        elif state == "speaking":
            orb.listening = False
            orb.thinking = False
            orb.speaking = True
            self.status = "Speaking"
            self.status_color = ACCENT
            self.orb_label = "Aizen is speaking..."

        else:
            orb.listening = False
            orb.thinking = False
            orb.speaking = False
            self.status = "Online"
            self.status_color = GREEN
            self.orb_label = "Aizen AI"

    def _voice_error(self):
        was_active = self.call_active
        self._voice_state("idle")

        if was_active:
            self.call_active = False
            self.subtitle = "Personal assistant"
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

    def toggle_call(self):
        if self.call_active:
            self.end_call()
        else:
            self.start_call()

    def start_call(self):
        if self.busy:
            return

        if platform != "android":
            self.add_bubble(
                "Voice is only available on the Android build.",
                mine=False
            )
            return

        if not check_permission(Permission.RECORD_AUDIO):
            request_permissions(
                [Permission.RECORD_AUDIO],
                lambda perms, grants: self._setup_android_voice()
            )
            self.add_bubble(
                "Please allow the microphone permission, then tap Call again.",
                mine=False
            )
            return

        if self._recognizer is None or self._tts is None:
            self._setup_android_voice()
            self.add_bubble(
                "Voice is getting ready. Tap Call again in a second.",
                mine=False
            )
            return

        self.call_active = True
        self.subtitle = "Voice call active"
        self.shrink_orb()
        self._begin_listening()

    def end_call(self):
        self.call_active = False
        self.subtitle = "Personal assistant"

        if self._speech_poll is not None:
            try:
                self._speech_poll.cancel()
            except Exception:
                pass
            self._speech_poll = None

        self._stop_listen()

        try:
            if self._tts is not None:
                self._tts.stop()
        except Exception:
            pass

        self._voice_state("idle")
