import json
import os
import tempfile
import threading
import urllib.error
import urllib.request

from kivy.clock import Clock
from kivy.core.audio import SoundLoader

WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev"

def speak(text, on_done=None):
text = str(text).strip()

if not text:
    return False

def finish():
    if on_done:
        try:
            on_done()
        except Exception as error:
            print("ELEVENLABS CALLBACK ERROR:", repr(error))

def run():
    audio_file = None
    sound = None

    try:
        payload = json.dumps({
            "text": text[:3500]
        }).encode("utf-8")

        request = urllib.request.Request(
            WORKER_URL + "/voice",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 13; Mobile) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0 Mobile Safari/537.36"
                ),
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:
            audio_data = response.read()

        if not audio_data:
            raise RuntimeError("No audio received")

        fd, audio_file = tempfile.mkstemp(
            suffix=".mp3"
        )
        os.close(fd)

        with open(audio_file, "wb") as file:
            file.write(audio_data)

        sound = SoundLoader.load(audio_file)

        if sound is None:
            raise RuntimeError(
                "Could not load ElevenLabs audio"
            )

        def cleanup():
            try:
                if audio_file and os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception:
                pass

        def check_audio(dt):
            try:
                if sound.state == "stop":
                    cleanup()
                    finish()
                    return False

            except Exception as error:
                print(
                    "AUDIO CHECK ERROR:",
                    repr(error)
                )
                cleanup()
                finish()
                return False

            return True

        sound.play()

        Clock.schedule_interval(
            check_audio,
            0.2
        )

    except urllib.error.HTTPError as error:
        try:
            details = error.read().decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            details = str(error)

        print(
            "Aizen ElevenLabs HTTP Error:",
            error.code,
            details
        )

        Clock.schedule_once(
            lambda dt: finish(),
            0
        )

    except Exception as error:
        print(
            "Aizen ElevenLabs Error:",
            repr(error)
        )

        Clock.schedule_once(
            lambda dt: finish(),
            0
        )

threading.Thread(
    target=run,
    daemon=True
).start()

return True
