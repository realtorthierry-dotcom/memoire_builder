from __future__ import annotations

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000  # Whisper expects mono audio sampled at 16kHz


class AudioRecorder:
    """Captures microphone audio into memory until stopped."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False

    def start(self) -> None:
        if self._recording:
            return
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._on_audio_block,
        )
        self._stream.start()
        self._recording = True

    def _on_audio_block(self, indata, frames, time_info, status) -> None:
        self._frames.append(indata.copy())

    def stop(self) -> np.ndarray:
        """Stops recording and returns the captured audio as a mono float32 array."""
        if not self._recording:
            return np.zeros(0, dtype="float32")
        self._recording = False
        self._stream.stop()
        self._stream.close()
        self._stream = None
        if not self._frames:
            return np.zeros(0, dtype="float32")
        return np.concatenate(self._frames, axis=0).reshape(-1)

    @property
    def is_recording(self) -> bool:
        return self._recording
