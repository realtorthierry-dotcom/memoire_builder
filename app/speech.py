from __future__ import annotations

import queue
import threading

import pyttsx3

# A slower pace reads as calmer and easier to follow, which matters more here
# than for a typical notification-style TTS use.
DEFAULT_RATE = 140  # words per minute (SAPI5 default is ~200)
PREFERRED_VOICE_KEYWORDS = ("david",)


class Speaker:
    """Speaks text aloud on a dedicated background thread so the GUI never blocks on it."""

    def __init__(self, rate: int = DEFAULT_RATE):
        self._rate = rate
        self._queue: queue.Queue[str] = queue.Queue()
        self._current_engine = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def say(self, text: str) -> None:
        if text:
            self._queue.put(text)

    def stop(self) -> None:
        """Cancels anything queued and interrupts speech currently playing."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        if self._current_engine is not None:
            self._current_engine.stop()

    def _run(self) -> None:
        while True:
            text = self._queue.get()
            # A fresh engine per utterance avoids a known SAPI5/pyttsx3 issue on
            # Windows where reusing one engine can silently stop producing audio
            # after its first runAndWait() call.
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            _select_preferred_voice(engine)
            self._current_engine = engine
            engine.say(text)
            engine.runAndWait()
            self._current_engine = None
            engine.stop()


def _select_preferred_voice(engine) -> None:
    for voice in engine.getProperty("voices"):
        name = (voice.name or "").lower()
        if any(keyword in name for keyword in PREFERRED_VOICE_KEYWORDS):
            engine.setProperty("voice", voice.id)
            return
