# aizen_voice.py - PART 2b: voice engine (mic + ElevenLabs)

from kivy.clock import Clock
from kivy.utils import platform

from aizen_call import CallMixin
from elevenlabs_voice import speak as elevenlabs_speak

if platform == "android":
    from jnius import autoclass
    from android.runnable import run_on_ui_thread
    from aizen_java import RecListener, TTSListener
else:
    def run_on_ui_thread(f):
        return f


class VoiceMixin(CallMixin):
    """Voice features used by the main Aizen screen."""

    def _init_voice(self):
        self._tts = None
        self._tts_ready = False
        self._tts_listener = None
        self._recognizer = None
        self._recognition_listener = None
        self._speech_poll = None
        self._speak_token = 0

    @run_on_ui_thread
    def _setup_android_voice(self, *args):
        if platform != "android":
            return

        if self._recognizer is not None and self._tts is not None:
            return

        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            # Keep Android TTS initialized for compatibility
            # with the existing voice system.
            self._tts_listener = TTSListener(self)

            self._tts = autoclass("android.speech.tts.TextToSpeech")(
                activity,
                self._tts_listener
            )

            SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")

            if not SpeechRecognizer.isRecognitionAvailable(activity):
                print("VOICE SETUP: speech recognition is not available")
                self._tts = None
                return

            self._recognizer = SpeechRecognizer.createSpeechRecognizer(activity)

            self._recognition_listener = RecListener(self)

            self._recognizer.setRecognitionListener(
                self._recognition_listener
            )

            print("VOICE SETUP: microphone ready")

        except Exception as e:
            print("VOICE SETUP ERROR:", e)

            self._tts = None
            self._recognizer = None

    @run_on_ui_thread
    def _listen(self, *args):
        if self._recognizer is None:
            return

        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            Intent = autoclass("android.content.Intent")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )

            # Indian English works better for Hinglish input.
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN")

            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)

            # Some phones need the calling package to be set.
            intent.putExtra(
                RecognizerIntent.EXTRA_CALLING_PACKAGE,
                activity.getPackageName(),
            )

            self._recognizer.startListening(intent)

        except Exception as e:
            print("LISTEN ERROR:", e)

            Clock.schedule_once(
                lambda dt: self._voice_error(),
                0
            )

    @run_on_ui_thread
    def _stop_listen(self, *args):
        try:
            if self._recognizer is not None:
                self._recognizer.cancel()

        except Exception as e:
            print("STOP LISTEN ERROR:", e)

    def _speak(self, text):
        """
        Play the AI response using the secure ElevenLabs
        Cloudflare Worker. After speaking, the call goes back to
        listening. If ElevenLabs fails or never answers, the call
        still continues instead of hanging.
        """

        if not text or not str(text).strip():
            return False

        text = str(text)[:3500]

        # One token per speech, so late/duplicate callbacks are ignored.
        self._speak_token += 1
        token = self._speak_token

        def finished(*args):
            # May be called from a background thread.
            Clock.schedule_once(lambda dt: self._after_speech(token), 0)

        # Safety net: if the audio callback never comes, continue anyway.
        watchdog_seconds = max(20, len(text) * 0.09 + 15)
        Clock.schedule_once(lambda dt: self._after_speech(token), watchdog_seconds)

        try:
            Clock.schedule_once(lambda dt: self._voice_state("speaking"), 0)

            elevenlabs_speak(text, on_done=finished)

            return True

        except Exception as e:
            print("ELEVENLABS SPEAK ERROR:", e)

            finished()

            return False

    def _after_speech(self, token):
        # Ignore if this speech was already finished or replaced.
        if token != self._speak_token:
            return

        self._speak_token += 1

        self._voice_state("idle")

        if self.call_active:
            Clock.schedule_once(lambda dt: self._begin_listening(), 0.4)

    def _start_poll(self, dt):
        # Kept for compatibility with the existing system.
        self._speech_poll = Clock.schedule_interval(
            self._poll_speech,
            0.3
        )

    def _poll_speech(self, dt):
        # ElevenLabs handles playback completion
        # through its callback.
        if self._speech_poll is not None:
            try:
                self._speech_poll.cancel()
            except Exception:
                pass

            self._speech_poll = None

        return False

    def _begin_listening(self):
        if not self.call_active:
            return

        self._voice_state("listening")
        self._listen()
            
