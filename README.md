# memoire_builder

A desktop app that lets someone record spoken memories with a microphone,
transcribes them to text, and saves them — organized by life category — so
they can eventually be compiled into a memoire ebook for family.

It was built for an elderly relative who may be bedridden or in a wheelchair,
so the interface favors a few large, simple controls over feature density,
and is meant to be usable independently, without a technical helper.

## How it works

1. Pick what the memory is about (category) and what language you'll speak in
   (or leave both on their defaults).
2. Optionally tap **Need an idea?** for a gentle prompt to talk about — it's
   both shown on screen and read aloud automatically.
3. Tap **Start Recording**, speak, then tap **Stop Recording**.
4. The app transcribes the recording locally (nothing is sent to the internet)
   and shows you the text. Fix anything that was misheard, or just save it as is.
5. Saved memories show up under **My Memories**, where they can be reopened,
   edited, or deleted later.

Conversation prompts and key status updates (recording started, listening,
saved, and any errors) are read aloud automatically using the computer's
built-in text-to-speech, in addition to being shown on screen. It defaults to
the "Microsoft David" voice at a slower, easier-to-follow pace (120 words per
minute, versus SAPI5's default of ~200) — adjust `DEFAULT_RATE` and
`PREFERRED_VOICE_KEYWORDS` at the top of `app/speech.py` to change the pace
or preferred voice.

Speech-to-text runs entirely on this computer using [OpenAI's Whisper
model](https://github.com/openai/whisper) — no account, API key, or ongoing
internet connection is needed once it's set up, and no audio ever leaves the
machine. It supports English, French, and Spanish (auto-detected by default,
or pick one explicitly on screen for better accuracy on short recordings).

Recordings and transcripts are **not** stored in this repository. They're
saved to `Documents`-style folder in the user's home directory instead
(`~/MemoireBuilder/memories` — on Windows that's `C:\Users\<you>\MemoireBuilder\memories`),
each as a `audio.wav` + `transcript.txt` pair, indexed in `index.json`.

Compiling saved memories into a finished ebook (chapters, formatting, cover,
EPUB/PDF export) is intentionally out of scope for this first version — it's
a natural follow-up once recording is working well day to day.

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

`openai-whisper` depends on PyTorch, which is a large download. If this
machine has no GPU (the common case for a home PC), install the smaller
CPU-only build first to save time and disk space:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

The first time the app transcribes a recording, it downloads the Whisper
"small" model (~500MB) to a local cache — this needs internet once. After
that, transcription works fully offline.

## Running the app

```bash
python main.py
```

## Running the tests

Tests cover the storage and prompts logic (pure Python, no microphone or
model required):

```bash
pip install -r requirements-dev.txt
python -m pytest
```
