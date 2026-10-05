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
            Intent = autoclass("android.content.Intent")

            RecognizerIntent = autoclass("android.speech.RecognizerIntent")

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )

            # Indian English works better for Hinglish input.
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "en-IN",
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_MAX_RESULTS,
                1,
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
        Play AI response using the secure ElevenLabs
        Cloudflare Worker.

        ElevenLabs API key and Voice ID stay on Cloudflare.
        They are NOT stored inside the APK.
        """

        if not text or not str(text).strip():
            return False

        try:
            self._voice_state("speaking")

            def finished():
                if not self.call_active:
                    self._voice_state("idle")
                    return

                self._voice_state("idle")

                Clock.schedule_once(
                    lambda dt: self._begin_listening(),
                    0.4
                )

            elevenlabs_speak(
                str(text)[:3500],
                on_done=finished
            )

            return True

        except Exception as e:
            print("ELEVENLABS SPEAK ERROR:", e)

            self._voice_state("idle")

            return False

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
    
