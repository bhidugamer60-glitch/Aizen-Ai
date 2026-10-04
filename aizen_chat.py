# aizen_chat.py  -  PART 3: config + sending messages to the AI
import json

from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest

try:
    import certifi
    CA_FILE = certifi.where()
except Exception:
    CA_FILE = None

# ---------------------------------------------------------------------------
# AIZEN CONFIG
# ---------------------------------------------------------------------------
WORKER_URL = "https://hidden-recipe-50cc.bhidugamer60.workers.dev"
MODEL = "openai/gpt-4o-mini:online"

SYSTEM_PROMPT = (
    "You are Aizen, a personal AI assistant. Reply in the same language "
    "the user writes in. If the user writes Hinglish, reply in Hinglish. "
    "Be clear, friendly, useful and concise. You can use web search when "
    "the user's request needs current information. Do not use markdown "
    "formatting."
)


class ChatMixin:
    """Chat/AI logic."""

    def send(self):
        text = self.ids.inp.text.strip()

        if not text or self.busy:
            return

        self.ids.inp.text = ""
        self.shrink_orb()
        self.add_bubble(text, mine=True)
        self.history.append({"role": "user", "content": text})

        self.set_state(True)
        self._typing = self.add_bubble("...", mine=False)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += self.history[-20:]

        payload = json.dumps({"model": MODEL, "messages": messages})

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Cloudflare blocks the default Python user agent (error 1010)
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 13; Mobile) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Mobile Safari/537.36"
            ),
        }

        UrlRequest(
            WORKER_URL,
            req_body=payload,
            req_headers=headers,
            method="POST",
            on_success=self._on_success,
            on_failure=self._on_failure,
            on_error=self._on_error,
            ca_file=CA_FILE,
            timeout=60,
        )

    def _extract_reply(self, result):
        if isinstance(result, (bytes, bytearray)):
            result = result.decode("utf-8", "ignore")
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                return result.strip()

        if isinstance(result, dict):
            try:
                return str(result["choices"][0]["message"]["content"]).strip()
            except Exception:
                pass
            if "error" in result:
                err = result["error"]
                if isinstance(err, dict):
                    err = err.get("message", err)
                return "Connection problem: %s" % err
            if "reply" in result:
                return str(result["reply"]).strip()

        return "I got an empty response. Please try again."

    def _finish_reply(self, reply, ok=True):
        if self._typing is not None:
            self._typing.text = reply
            self._typing = None
        else:
            self.add_bubble(reply, mine=False)

        Clock.schedule_once(self._scroll_down, 0.08)

        if ok:
            self.history.append({"role": "assistant", "content": reply})

        self.set_state(False)

        if self.call_active:
            if ok and self._speak(reply):
                return
            # could not speak or request failed: keep the call alive
            if self.call_active:
                Clock.schedule_once(lambda dt: self._begin_listening(), 0.4)

    def _on_success(self, req, result):
        reply = self._extract_reply(result)
        self._finish_reply(reply, ok=True)

    def _on_failure(self, req, result):
        code = getattr(req, "resp_status", "?")
        detail = ""
        if isinstance(result, dict):
            detail = str(result.get("error", ""))
        elif result:
            detail = str(result)[:120]
        self._finish_reply(
            "Connection problem. HTTP %s %s" % (code, detail),
            ok=False
        )

    def _on_error(self, req, error):
        self._finish_reply("Connection problem: %s" % error, ok=False)
