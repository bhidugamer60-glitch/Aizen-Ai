# aizen_java.py - Android listeners (speech recognition + TTS init)
#
# IMPORTANT: Android calls these methods on its own thread, NOT the Kivy
# thread. Every touch of the UI goes through Clock.schedule_once.

from jnius import PythonJavaClass, java_method, autoclass
from kivy.clock import Clock

ERROR_NAMES = {
    1: "network timeout",
    2: "network error",
    3: "audio error",
    4: "server error",
    5: "client error",
    6: "no speech heard",
    7: "no match",
    8: "recognizer busy",
    9: "microphone permission missing",
    10: "too many requests",
    11: "server disconnected",
    12: "language not supported",
    13: "language unavailable",
}

# Errors where it is fine to just listen again during a call.
SOFT_ERRORS = (6, 7)
MAX_SOFT_RETRIES = 2


class RecListener(PythonJavaClass):
    __javainterfaces__ = ["android/speech/RecognitionListener"]
    __javacontext__ = "app"

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.retries = 0

    @java_method("(Landroid/os/Bundle;)V")
    def onReadyForSpeech(self, params):
        print("REC: ready for speech")

    @java_method("()V")
    def onBeginningOfSpeech(self):
        print("REC: speech started")
        self.retries = 0

    @java_method("(F)V")
    def onRmsChanged(self, rms):
        pass

    @java_method("([B)V")
    def onBufferReceived(self, buffer):
        pass

    @java_method("()V")
    def onEndOfSpeech(self):
        print("REC: speech ended")

    @java_method("(Landroid/os/Bundle;)V")
    def onPartialResults(self, partial):
        pass

    @java_method("(ILandroid/os/Bundle;)V")
    def onEvent(self, event_type, params):
        pass

    @java_method("(I)V")
    def onError(self, error):
        name = ERROR_NAMES.get(error, "unknown")
        print("REC ERROR:", error, name)

        owner = self.owner

        # No speech / no match: keep the call alive, listen again.
        if error in SOFT_ERRORS and owner.call_active:
            if self.retries < MAX_SOFT_RETRIES:
                self.retries += 1
                Clock.schedule_once(lambda dt: owner._begin_listening(), 0.3)
                return

        # Recognizer busy: cancel and try once more.
        if error == 8 and owner.call_active and self.retries < MAX_SOFT_RETRIES:
            self.retries += 1
            owner._stop_listen()
            Clock.schedule_once(lambda dt: owner._begin_listening(), 0.6)
            return

        self.retries = 0

        # Real problem: tell the user the actual reason.
        if error not in SOFT_ERRORS:
            def show(dt):
                try:
                    owner.add_bubble(
                        "Mic error: %s (code %d)" % (name, error),
                        mine=False,
                    )
                except Exception as e:
                    print("REC bubble error:", e)

            Clock.schedule_once(show, 0)

        Clock.schedule_once(lambda dt: owner._voice_error(), 0)

    @java_method("(Landroid/os/Bundle;)V")
    def onResults(self, results):
        text = ""

        try:
            SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")
            matches = results.getStringArrayList(
                SpeechRecognizer.RESULTS_RECOGNITION
            )

            if matches is not None and matches.size() > 0:
                text = str(matches.get(0))

        except Exception as e:
            print("REC RESULT ERROR:", e)

        print("REC RESULT:", text)

        self.retries = 0
        owner = self.owner
        Clock.schedule_once(lambda dt: owner._voice_result(text), 0)


class TTSListener(PythonJavaClass):
    __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
    __javacontext__ = "app"

    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    @java_method("(I)V")
    def onInit(self, status):
        # status 0 == SUCCESS
        self.owner._tts_ready = (status == 0)
        print("TTS INIT:", status)
    
