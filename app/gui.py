from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox

from .prompts import CATEGORIES, random_prompt
from .recorder import SAMPLE_RATE, AudioRecorder
from .storage import MemoryStore
from .transcriber import LANGUAGE_CODES, Transcriber

BG = "#fdfcf7"
FG = "#1a1a1a"
MUTED = "#6b6b6b"
ACCENT = "#2e7d32"
STOP = "#c62828"
BUTTON_BG = "#e8e6da"

TITLE_FONT = ("Segoe UI", 28, "bold")
HEADING_FONT = ("Segoe UI", 22, "bold")
BODY_FONT = ("Segoe UI", 16)
SMALL_FONT = ("Segoe UI", 13)
BIG_BUTTON_FONT = ("Segoe UI", 20, "bold")
PROMPT_FONT = ("Segoe UI", 15, "italic")


class MemoireApp:
    """Top-level controller: owns app state and switches between full-window pages."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("My Memoire")
        self.root.configure(bg=BG)
        self.root.geometry("820x700")
        self.root.minsize(700, 600)

        self.recorder = AudioRecorder(SAMPLE_RATE)
        self.transcriber = Transcriber()
        self.store = MemoryStore()

        self.selected_category = tk.StringVar(value=CATEGORIES[0])
        self.selected_language = tk.StringVar(value="Auto-detect")
        self.current_prompt = tk.StringVar(value="")

        self._pending_audio = None

        container = tk.Frame(root, bg=BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames: dict[type, tk.Frame] = {}
        for page_cls in (RecordPage, ReviewPage, MemoriesPage):
            frame = page_cls(container, self)
            self.frames[page_cls] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show(RecordPage)

    def show(self, page_cls: type, **kwargs) -> None:
        frame = self.frames[page_cls]
        on_show = getattr(frame, "on_show", None)
        if on_show is not None:
            on_show(**kwargs)
        frame.tkraise()

    # --- recording flow ----------------------------------------------------

    def start_recording(self) -> None:
        try:
            self.recorder.start()
        except Exception as exc:
            messagebox.showerror("Microphone problem", f"Could not start recording:\n{exc}")
            return
        self.frames[RecordPage].on_recording_started()

    def stop_recording(self) -> None:
        audio = self.recorder.stop()
        if audio.size == 0:
            self.frames[RecordPage].on_show()
            messagebox.showinfo("No audio", "It looks like nothing was recorded. Please try again.")
            return
        self.frames[RecordPage].on_recording_stopped()
        self._pending_audio = audio
        language_code = LANGUAGE_CODES.get(self.selected_language.get())
        threading.Thread(target=self._transcribe, args=(audio, language_code), daemon=True).start()

    def _transcribe(self, audio, language_code: str | None) -> None:
        try:
            text, _detected = self.transcriber.transcribe(audio, language_code)
        except Exception as exc:
            self.root.after(0, lambda: self._on_transcribe_error(exc))
            return
        self.root.after(0, lambda: self._on_transcribed(text))

    def _on_transcribe_error(self, exc: Exception) -> None:
        self._pending_audio = None
        self.frames[RecordPage].on_show()
        messagebox.showerror("Transcription problem", str(exc))

    def _on_transcribed(self, text: str) -> None:
        self.show(ReviewPage, transcript=text)

    def save_reviewed_memory(self, transcript: str) -> None:
        self.store.save(
            self._pending_audio,
            SAMPLE_RATE,
            transcript,
            category=self.selected_category.get(),
            language=self.selected_language.get(),
        )
        self._pending_audio = None
        self.current_prompt.set("")
        self.show(RecordPage)

    def discard_pending_recording(self) -> None:
        self._pending_audio = None
        self.show(RecordPage)

    def new_prompt(self) -> None:
        self.current_prompt.set(random_prompt(self.selected_category.get()))


class RecordPage(tk.Frame):
    """Home screen: pick a category/language, get an idea, start recording."""

    def __init__(self, parent: tk.Widget, app: MemoireApp):
        super().__init__(parent, bg=BG)
        self.app = app

        tk.Label(self, text="My Memoire", font=TITLE_FONT, bg=BG, fg=FG).pack(pady=(30, 5))
        tk.Label(
            self,
            text="Press the button below and start talking about your life.",
            font=BODY_FONT,
            bg=BG,
            fg=FG,
            wraplength=680,
            justify="center",
        ).pack(pady=(0, 20))

        options = tk.Frame(self, bg=BG)
        options.pack(pady=(0, 10))

        tk.Label(options, text="This memory is about:", font=SMALL_FONT, bg=BG, fg=FG).grid(
            row=0, column=0, sticky="e", padx=5, pady=5
        )
        tk.OptionMenu(options, app.selected_category, *CATEGORIES).grid(
            row=0, column=1, sticky="w", padx=5, pady=5
        )

        tk.Label(options, text="Speaking in:", font=SMALL_FONT, bg=BG, fg=FG).grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )
        tk.OptionMenu(options, app.selected_language, *LANGUAGE_CODES.keys()).grid(
            row=1, column=1, sticky="w", padx=5, pady=5
        )

        tk.Label(
            self,
            textvariable=app.current_prompt,
            font=PROMPT_FONT,
            bg=BG,
            fg=ACCENT,
            wraplength=680,
            justify="center",
        ).pack(pady=(5, 5))

        tk.Button(
            self,
            text="Need an idea?",
            font=SMALL_FONT,
            command=app.new_prompt,
            bg=BUTTON_BG,
            fg=FG,
            relief="flat",
            padx=10,
            pady=4,
        ).pack(pady=(0, 20))

        self.record_button = tk.Button(
            self,
            text="\U0001F3A4  Start Recording",
            font=BIG_BUTTON_FONT,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT,
            activeforeground="white",
            height=2,
            width=24,
            relief="flat",
            command=self._toggle,
        )
        self.record_button.pack(pady=10)

        self.status_label = tk.Label(self, text="Ready", font=BODY_FONT, bg=BG, fg=MUTED)
        self.status_label.pack(pady=(10, 20))

        tk.Button(
            self,
            text="My Memories",
            font=BODY_FONT,
            command=lambda: app.show(MemoriesPage),
            bg=BUTTON_BG,
            fg=FG,
            relief="flat",
            padx=16,
            pady=8,
        ).pack(side="bottom", pady=20)

    def _toggle(self) -> None:
        if not self.app.recorder.is_recording:
            self.app.start_recording()
        else:
            self.app.stop_recording()

    def on_recording_started(self) -> None:
        self.record_button.config(text="⏹  Stop Recording", bg=STOP, activebackground=STOP)
        self.status_label.config(text="Recording... speak naturally, take your time.")

    def on_recording_stopped(self) -> None:
        self.record_button.config(
            text="\U0001F3A4  Start Recording", bg=ACCENT, activebackground=ACCENT, state="disabled"
        )
        self.status_label.config(text="Listening to what you said... this can take a minute.")

    def on_show(self) -> None:
        self.record_button.config(
            text="\U0001F3A4  Start Recording", bg=ACCENT, activebackground=ACCENT, state="normal"
        )
        self.status_label.config(text="Ready")


class ReviewPage(tk.Frame):
    """Shows the transcript after recording; editing is optional before saving."""

    def __init__(self, parent: tk.Widget, app: MemoireApp):
        super().__init__(parent, bg=BG)
        self.app = app

        tk.Label(self, text="Here's what I heard:", font=HEADING_FONT, bg=BG, fg=FG).pack(pady=(30, 5))
        tk.Label(
            self,
            text="Feel free to fix anything, or just save it as it is.",
            font=BODY_FONT,
            bg=BG,
            fg=MUTED,
        ).pack(pady=(0, 15))

        text_frame = tk.Frame(self, bg=BG)
        text_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        self.text = tk.Text(
            text_frame,
            wrap="word",
            font=("Segoe UI", 15),
            yscrollcommand=scrollbar.set,
            padx=10,
            pady=10,
        )
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.text.yview)

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=(0, 30))

        tk.Button(
            button_row,
            text="✔  Save This Memory",
            font=BIG_BUTTON_FONT,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT,
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=10,
            command=self._save,
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            button_row,
            text="Discard & Try Again",
            font=BODY_FONT,
            bg=BUTTON_BG,
            fg=FG,
            relief="flat",
            padx=16,
            pady=10,
            command=app.discard_pending_recording,
        ).grid(row=0, column=1, padx=10)

    def on_show(self, transcript: str = "") -> None:
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", transcript)

    def _save(self) -> None:
        transcript = self.text.get("1.0", tk.END).strip()
        if not transcript and not messagebox.askyesno(
            "Empty memory", "No words were recognized. Save anyway?"
        ):
            return
        self.app.save_reviewed_memory(transcript)


class MemoriesPage(tk.Frame):
    """Lists saved memories; double-click one to view, edit, or delete it."""

    def __init__(self, parent: tk.Widget, app: MemoireApp):
        super().__init__(parent, bg=BG)
        self.app = app
        self._memories: list = []

        tk.Label(self, text="My Memories", font=HEADING_FONT, bg=BG, fg=FG).pack(pady=(25, 15))

        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.listbox = tk.Listbox(
            list_frame, font=("Segoe UI", 14), yscrollcommand=scrollbar.set, activestyle="none"
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", self._open_selected)
        scrollbar.config(command=self.listbox.yview)

        tk.Button(
            self,
            text="Back",
            font=BODY_FONT,
            command=lambda: app.show(RecordPage),
            bg=BUTTON_BG,
            fg=FG,
            relief="flat",
            padx=16,
            pady=8,
        ).pack(side="bottom", pady=20)

    def on_show(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        self._memories = list(reversed(self.app.store.list_all()))
        self.listbox.delete(0, tk.END)
        if not self._memories:
            self.listbox.insert(tk.END, "No memories saved yet. Record your first one!")
            return
        for memory in self._memories:
            date = memory.timestamp.split("T")[0]
            preview = memory.preview or "(no speech detected)"
            self.listbox.insert(tk.END, f"[{memory.category}]  {date}  —  {preview}")

    def _open_selected(self, _event) -> None:
        if not self._memories:
            return
        selection = self.listbox.curselection()
        if not selection:
            return
        MemoryDetailWindow(self.app, self._memories[selection[0]], on_change=self.refresh)


class MemoryDetailWindow(tk.Toplevel):
    """Popup for viewing, editing, or deleting a single saved memory."""

    def __init__(self, app: MemoireApp, memory, on_change):
        super().__init__(app.root)
        self.app = app
        self.memory = memory
        self.on_change = on_change

        self.title(f"{memory.category} — {memory.timestamp.split('T')[0]}")
        self.configure(bg=BG)
        self.geometry("620x540")

        tk.Label(
            self,
            text=f"{memory.category}  ·  {memory.timestamp.split('T')[0]}",
            font=("Segoe UI", 16, "bold"),
            bg=BG,
            fg=FG,
        ).pack(pady=(15, 10))

        text_frame = tk.Frame(self, bg=BG)
        text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        self.text = tk.Text(
            text_frame, wrap="word", font=("Segoe UI", 13), yscrollcommand=scrollbar.set, padx=8, pady=8
        )
        self.text.insert("1.0", app.store.load_transcript(memory))
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.text.yview)

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=(0, 20))

        tk.Button(
            button_row,
            text="Save Changes",
            font=SMALL_FONT,
            bg=ACCENT,
            fg="white",
            relief="flat",
            padx=14,
            pady=6,
            command=self._save_changes,
        ).grid(row=0, column=0, padx=8)
        tk.Button(
            button_row,
            text="Delete This Memory",
            font=SMALL_FONT,
            bg=STOP,
            fg="white",
            relief="flat",
            padx=14,
            pady=6,
            command=self._delete,
        ).grid(row=0, column=1, padx=8)
        tk.Button(
            button_row,
            text="Close",
            font=SMALL_FONT,
            bg=BUTTON_BG,
            fg=FG,
            relief="flat",
            padx=14,
            pady=6,
            command=self.destroy,
        ).grid(row=0, column=2, padx=8)

    def _save_changes(self) -> None:
        new_text = self.text.get("1.0", tk.END).strip()
        self.app.store.update_transcript(self.memory.id, new_text)
        self.on_change()
        messagebox.showinfo("Saved", "Your changes have been saved.")

    def _delete(self) -> None:
        if messagebox.askyesno(
            "Delete memory", "Are you sure you want to delete this memory? This can't be undone."
        ):
            self.app.store.delete(self.memory.id)
            self.on_change()
            self.destroy()
