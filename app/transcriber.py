from __future__ import annotations

import numpy as np
import whisper

# Maps the language picker's on-screen labels to Whisper language codes.
# None means "auto-detect", which Whisper does from the first ~30 seconds of audio.
LANGUAGE_CODES = {
    "Auto-detect": None,
    "English": "en",
    "Français": "fr",
    "Español": "es",
}


class Transcriber:
    """Wraps a local Whisper model for fully offline, multilingual speech-to-text."""

    def __init__(self, model_name: str = "small"):
        self._model_name = model_name
        self._model = None  # loaded lazily so the GUI can open instantly

    def _ensure_loaded(self):
        if self._model is None:
            self._model = whisper.load_model(self._model_name)
        return self._model

    def transcribe(self, audio: np.ndarray, language: str | None = None) -> tuple[str, str]:
        """Transcribes mono float32 audio (16kHz). Returns (text, detected_language_code)."""
        if audio.size == 0:
            return "", ""
        model = self._ensure_loaded()
        # Passing a numpy array (rather than a file path) skips Whisper's
        # ffmpeg-based audio loader entirely, so no external ffmpeg install is needed.
        result = model.transcribe(audio, fp16=False, language=language)
        return result["text"].strip(), result.get("language", language or "")
