import threading
import tempfile
import os
import urllib.request
import urllib.error

from kivy.clock import Clock
from kivy.core.audio import SoundLoader


WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev"


def speak(text, on_done=None):
    if not text or not text.strip():
        return

    def run():
        audio_file = None
        sound = None

        try:
            data = text.encode("utf-8")

            request = urllib.request.Request(
                WORKER_URL + "/voice",
                data=(
                    b'{"text": ' +
                    __import__("json").dumps(text).encode("utf-8") +
                    b"}"
                ),
                headers={
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=60) as response:
                audio_data = response.read()

            if not audio_data:
                raise RuntimeError("No audio received")

            fd, audio_file = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

            with open(audio_file, "wb") as file:
                file.write(audio_data)

            sound = SoundLoader.load(audio_file)

            if sound is None:
                raise RuntimeError("Could not load audio")

            sound.play()

            def check_audio(dt):
                if sound.state == "stop":
                    try:
                        if audio_file and os.path.exists(audio_file):
                            os.remove(audio_file)
                    except Exception:
                        pass

                    if on_done:
                        on_done()

                    return False

                return True

            Clock.schedule_interval(check_audio, 0.2)

        except urllib.error.HTTPError as error:
            try:
                details = error.read().decode("utf-8", errors="replace")
            except Exception:
                details = str(error)

            print("Aizen ElevenLabs HTTP Error:", error.code, details)

        except Exception as error:
            print("Aizen ElevenLabs Error:", repr(error))

    threading.Thread(target=run, daemon=True).start()
