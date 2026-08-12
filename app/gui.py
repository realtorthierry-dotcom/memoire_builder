from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox

from .prompts import (
    category_from_option,
    category_options,
    random_prompt,
    spoken_category_list,
)
from .recorder import SAMPLE_RATE, AudioRecorder
from .speech import Speaker
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
        self.root.title("My Memoires")
        self.root.configure(bg=BG)
        self.root.geometry("820x700")
        self.root.minsize(700, 600)
        # Start maximized so nothing (like the Save button below the transcript)
        # can end up clipped off the bottom on a smaller or unusual screen.
        self.root.state("zoomed")

        self.recorder = AudioRecorder(SAMPLE_RATE)
        self.transcriber = Transcriber()
        self.store = MemoryStore()
        self.speaker = Speaker()

        default_category_option = next(
            option for option in category_options() if category_from_option(option) == "Freeform"
        )
        self.selected_category = tk.StringVar(value=default_category_option)
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
        # Cut off any category prompt or confirmation still being read aloud,
        # so it doesn't keep talking over her while she's trying to record.
        self.speaker.stop()
        try:
            self.recorder.start()
        except Exception as exc:
            self.speaker.say("There was a problem with the microphone.")
            messagebox.showerror("Microphone problem", f"Could not start recording:\n{exc}")
            return
        self.frames[RecordPage].on_recording_started()

    def stop_recording(self) -> None:
        audio = self.recorder.stop()
        if audio.size == 0:
            self.frames[RecordPage].on_show()
            self.speaker.say("It looks like nothing was recorded. Please try again.")
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
        self.speaker.say("There was a problem understanding the recording.")
        messagebox.showerror("Transcription problem", str(exc))

    def _on_transcribed(self, text: str) -> None:
        self.show(ReviewPage, transcript=text)

    def save_reviewed_memory(self, transcript: str) -> None:
        self.store.save(
            self._pending_audio,
            SAMPLE_RATE,
            transcript,
            category=category_from_option(self.selected_category.get()),
            language=self.selected_language.get(),
        )
        self._pending_audio = None
        self.current_prompt.set("")
        self.show(RecordPage, status="Saved! Ready for your next memory.")
        self.root.after(2500, lambda: self.frames[RecordPage].set_status("Ready", speak=False))

    def discard_pending_recording(self) -> None:
        self._pending_audio = None
        self.show(RecordPage)

    def new_prompt(self) -> None:
        prompt = random_prompt(category_from_option(self.selected_category.get()))
        self.current_prompt.set(prompt)
        self.speaker.say(prompt)


class RecordPage(tk.Frame):
    """Home screen: pick a category/language, get an idea, start recording."""

    def __init__(self, parent: tk.Widget, app: MemoireApp):
        super().__init__(parent, bg=BG)
        self.app = app

        # Packed before everything else below, so these buttons always get
        # their space at the bottom and can never be pushed off a shorter window.
        bottom_buttons = tk.Frame(self, bg=BG)
        bottom_buttons.pack(side="bottom", pady=20)

        tk.Button(
            bottom_buttons,
            text="My Memories",
            font=BODY_FONT,
            command=lambda: app.show(MemoriesPage),
            bg=BUTTON_BG,
            fg=FG,
            relief="flat",
            padx=16,
            pady=8,
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            bottom_buttons,
            text="Exit",
            font=BODY_FONT,
            command=self._exit_app,
            bg=BUTTON_BG,
            fg=FG,
            relief="flat",
            padx=16,
            pady=8,
        ).grid(row=0, column=1, padx=10)

        tk.Label(self, text="My Memoires", font=TITLE_FONT, bg=BG, fg=FG).pack(pady=(30, 5))
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
        tk.OptionMenu(
            options, app.selected_category, *category_options(), command=self._on_category_chosen
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

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

    def _toggle(self) -> None:
        if not self.app.recorder.is_recording:
            self.app.start_recording()
        else:
            self.app.stop_recording()

    def _on_category_chosen(self, selected_option: str) -> None:
        category = category_from_option(selected_option)
        self.set_status(f"You chose {category}. Start speaking whenever you're ready.")

    def _exit_app(self) -> None:
        if messagebox.askyesno("Exit", "Are you sure you want to exit My Memoires?"):
            self.app.root.destroy()

    def on_recording_started(self) -> None:
        self.record_button.config(text="⏹  Stop Recording", bg=STOP, activebackground=STOP)
        self.set_status("Recording... speak naturally, take your time.")

    def on_recording_stopped(self) -> None:
        self.record_button.config(
            text="\U0001F3A4  Start Recording", bg=ACCENT, activebackground=ACCENT, state="disabled"
        )
        self.set_status("Listening to what you said... this can take a minute to transcribe to text.")

    def on_show(self, status: str | None = None) -> None:
        self.record_button.config(
            text="\U0001F3A4  Start Recording", bg=ACCENT, activebackground=ACCENT, state="normal"
        )
        # Only speak the status when arriving with an explicit message (e.g.
        # "Saved!") — plain navigation back to this page shouldn't narrate
        # "Ready" every time. The category prompt, however, is asked every
        # time she's back at this screen ready to record again.
        self.set_status(status or "Ready", speak=status is not None)
        self.app.speaker.say(spoken_category_list())

    def set_status(self, text: str, speak: bool = True) -> None:
        self.status_label.config(text=text)
        if speak:
            self.app.speaker.say(text)


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

        # Packed (and anchored to the bottom) before the expanding text box
        # below, so these buttons always get their space and can never be
        # pushed off the bottom of a shorter window.
        button_row = tk.Frame(self, bg=BG)
        button_row.pack(side="bottom", pady=(10, 30))

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

        # Packed before the expanding list below, so Back always gets its
        # space and can never be pushed off the bottom of a shorter window.
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
