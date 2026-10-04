# aizen_voice.py  -  PART 2b: voice engine (mic + speech)
from kivy.clock import Clock
from kivy.utils import platform

from aizen_call import CallMixin

if platform == "android":
    from jnius import autoclass
    from android.runnable import run_on_ui_thread
    from aizen_java import RecListener, TTSListener
else:
    def run_on_ui_thread(f):
        return f


class VoiceMixin(CallMixin):
    """Voice features. Root(VoiceMixin, ChatMixin, BoxLayout) in main.py uses these."""

    def _init_voice(self):
        self._tts = None
        self._tts_ready = False
        self._tts_listener = None
        self._recognizer = None
        self._recognition_listener = None
        self._speech_poll = None

    @run_on_ui_thread
    def _setup_android_voice(self, *args):
        if platform != "android":
            return
        if self._recognizer is not None and self._tts is not None:
            return
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            # keep references alive, otherwise Java callbacks crash
            self._tts_listener = TTSListener(self)
            self._tts = autoclass("android.speech.tts.TextToSpeech")(
                activity, self._tts_listener
            )

            SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")
            if not SpeechRecognizer.isRecognitionAvailable(activity):
                print("VOICE SETUP: recognition not available on this device")
                self._tts = None
                return

            self._recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            self._recognition_listener = RecListener(self)
            self._recognizer.setRecognitionListener(self._recognition_listener)

        except Exception as e:
            print("VOICE SETUP ERROR:", e)
            self._tts = None
            self._recognizer = None

    @run_on_ui_thread
    def _listen(self, *args):
        if self._recognizer is None:
            return
        try:
            Intent = autoclass("android.content.Intent")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN")
            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            self._recognizer.startListening(intent)
        except Exception as e:
            print("LISTEN ERROR:", e)
            Clock.schedule_once(lambda dt: self._voice_error(), 0)

    @run_on_ui_thread
    def _stop_listen(self, *args):
        try:
            if self._recognizer is not None:
                self._recognizer.cancel()
        except Exception as e:
            print("STOP LISTEN ERROR:", e)

    def _speak(self, text):
        if self._tts is None:
            return False
        try:
            self._tts.speak(str(text)[:3500], 0, None, "aizen")
            self._voice_state("speaking")
            if self._speech_poll is not None:
                self._speech_poll.cancel()
            # give TTS a moment to start before polling isSpeaking()
            self._speech_poll = Clock.schedule_once(self._start_poll, 0.8)
            return True
        except Exception as e:
            print("SPEAK ERROR:", e)
            return False

    def _start_poll(self, dt):
        self._speech_poll = Clock.schedule_interval(self._poll_speech, 0.3)

    def _poll_speech(self, dt):
        try:
            speaking = bool(self._tts.isSpeaking())
        except Exception:
            speaking = False

        if speaking:
            return True

        self._speech_poll = None
        self._voice_state("idle")

        if self.call_active:
            Clock.schedule_once(lambda d: self._begin_listening(), 0.4)
        return False

    def _begin_listening(self):
        if not self.call_active:
            return
        self._voice_state("listening")
        self._listen()
