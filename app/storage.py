from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

# Memories live outside the git repo, in the user's home directory, so personal
# recordings and transcripts are never accidentally committed or pushed anywhere.
DEFAULT_STORAGE_DIR = Path.home() / "MemoireBuilder" / "memories"

_PREVIEW_WORD_COUNT = 15


@dataclass
class Memory:
    id: str
    timestamp: str
    category: str
    language: str
    preview: str
    transcript_path: str
    audio_path: str


class MemoryStore:
    """Saves, lists, edits, and deletes recorded memories on disk."""

    def __init__(self, storage_dir: Path = DEFAULT_STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_dir / "index.json"

    def save(
        self,
        audio: np.ndarray,
        sample_rate: int,
        transcript: str,
        category: str = "General",
        language: str = "",
    ) -> Memory:
        memory_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        entry_dir = self.storage_dir / memory_id
        entry_dir.mkdir(parents=True, exist_ok=True)

        audio_path = entry_dir / "audio.wav"
        transcript_path = entry_dir / "transcript.txt"

        if audio.size:
            sf.write(audio_path, audio, sample_rate)
        transcript_path.write_text(transcript, encoding="utf-8")

        memory = Memory(
            id=memory_id,
            timestamp=datetime.now().isoformat(),
            category=category,
            language=language,
            preview=_preview_of(transcript),
            transcript_path=str(transcript_path),
            audio_path=str(audio_path),
        )
        entries = self.list_all()
        entries.append(memory)
        self._write_index(entries)
        return memory

    def list_all(self) -> list[Memory]:
        if not self.index_path.exists():
            return []
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        return [Memory(**item) for item in data]

    def load_transcript(self, memory: Memory) -> str:
        return Path(memory.transcript_path).read_text(encoding="utf-8")

    def update_transcript(self, memory_id: str, new_text: str) -> None:
        entries = self.list_all()
        for entry in entries:
            if entry.id == memory_id:
                Path(entry.transcript_path).write_text(new_text, encoding="utf-8")
                entry.preview = _preview_of(new_text)
        self._write_index(entries)

    def delete(self, memory_id: str) -> None:
        entries = [entry for entry in self.list_all() if entry.id != memory_id]
        self._write_index(entries)
        entry_dir = self.storage_dir / memory_id
        if entry_dir.exists():
            shutil.rmtree(entry_dir)

    def _write_index(self, entries: list[Memory]) -> None:
        self.index_path.write_text(
            json.dumps([asdict(entry) for entry in entries], indent=2),
            encoding="utf-8",
        )


def _preview_of(transcript: str) -> str:
    return " ".join(transcript.split()[:_PREVIEW_WORD_COUNT])
