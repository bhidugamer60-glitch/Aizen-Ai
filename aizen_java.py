# aizen_java.py  -  PART 2a: Android Java listeners (only used on the phone)
from kivy.clock import Clock
from kivy.utils import platform

if platform == "android":
    from jnius import PythonJavaClass, java_method


# ---------------------------------------------------------------------------
# Java listeners (must subclass PythonJavaClass, defined at module level)
# ---------------------------------------------------------------------------
if platform == "android":

    class TTSListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
        __javacontext__ = "app"

        def __init__(self, root):
            super().__init__()
            self.root = root

        @java_method("(I)V")
        def onInit(self, status):
            # status 0 == TextToSpeech.SUCCESS
            self.root._tts_ready = (status == 0)

    class RecListener(PythonJavaClass):
        __javainterfaces__ = ["android/speech/RecognitionListener"]
        __javacontext__ = "app"

        def __init__(self, root):
            super().__init__()
            self.root = root

        @java_method("(Landroid/os/Bundle;)V")
        def onReadyForSpeech(self, params):
            Clock.schedule_once(lambda dt: self.root._voice_state("listening"), 0)

        @java_method("()V")
        def onBeginningOfSpeech(self):
            Clock.schedule_once(lambda dt: self.root._voice_state("listening"), 0)

        @java_method("(F)V")
        def onRmsChanged(self, rms):
            pass

        @java_method("([B)V")
        def onBufferReceived(self, buf):
            pass

        @java_method("()V")
        def onEndOfSpeech(self):
            Clock.schedule_once(lambda dt: self.root._voice_state("thinking"), 0)

        @java_method("(I)V")
        def onError(self, error):
            Clock.schedule_once(lambda dt: self.root._voice_error(), 0)

        @java_method("(Landroid/os/Bundle;)V")
        def onResults(self, results):
            try:
                matches = results.getStringArrayList("results_recognition")
                if matches is not None and matches.size() > 0:
                    text = str(matches.get(0))
                    Clock.schedule_once(lambda dt: self.root._voice_result(text), 0)
                    return
            except Exception as e:
                print("VOICE RESULT ERROR:", e)
            Clock.schedule_once(lambda dt: self.root._voice_error(), 0)

        @java_method("(Landroid/os/Bundle;)V")
        def onPartialResults(self, partial):
            pass

        @java_method("(ILandroid/os/Bundle;)V")
        def onEvent(self, event_type, params):
            pass
