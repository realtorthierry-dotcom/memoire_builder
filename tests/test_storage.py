from __future__ import annotations

from pathlib import Path

import numpy as np

from app.storage import MemoryStore


def _silence(seconds: float = 0.1, sample_rate: int = 16000) -> np.ndarray:
    return np.zeros(int(seconds * sample_rate), dtype="float32")


def test_save_creates_transcript_and_audio_files(tmp_path):
    store = MemoryStore(storage_dir=tmp_path)

    memory = store.save(
        _silence(),
        sample_rate=16000,
        transcript="I grew up on a small farm.",
        category="Childhood",
        language="English",
    )

    assert memory.category == "Childhood"
    assert memory.preview == "I grew up on a small farm."
    assert Path(memory.transcript_path).read_text(encoding="utf-8") == "I grew up on a small farm."
    assert Path(memory.audio_path).exists()


def test_list_all_returns_saved_memories_in_order(tmp_path):
    store = MemoryStore(storage_dir=tmp_path)

    store.save(_silence(), 16000, "First memory.", category="General", language="English")
    store.save(_silence(), 16000, "Second memory.", category="Family", language="English")

    memories = store.list_all()

    assert [memory.preview for memory in memories] == ["First memory.", "Second memory."]


def test_update_transcript_rewrites_file_and_preview(tmp_path):
    store = MemoryStore(storage_dir=tmp_path)
    memory = store.save(_silence(), 16000, "Original text.", category="General", language="English")

    store.update_transcript(memory.id, "Corrected text.")

    updated = store.list_all()[0]
    assert updated.preview == "Corrected text."
    assert Path(updated.transcript_path).read_text(encoding="utf-8") == "Corrected text."


def test_delete_removes_entry_and_files(tmp_path):
    store = MemoryStore(storage_dir=tmp_path)
    memory = store.save(_silence(), 16000, "To be deleted.", category="General", language="English")

    store.delete(memory.id)

    assert store.list_all() == []
    assert not Path(memory.transcript_path).exists()
