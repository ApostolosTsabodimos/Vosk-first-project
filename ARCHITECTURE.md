# Architecture

This document explains how Voice to Cursor works internally — how the components connect, what each file does, and how data flows from your voice to text in the editor.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Code OSS                                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  VS Code Extension (extension.ts)                         │  │
│  │                                                           │  │
│  │  Ctrl+Alt+D ──► toggle() ──► send start/stop via WS      │  │
│  │                                                           │  │
│  │  WS message ──► insertText() ──► editor.edit().insert()   │  │
│  │                                                           │  │
│  │  Status Bar: disconnected │ ready │ recording │ transcr.  │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         │ WebSocket (ws://localhost:9876)        │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│  Python Backend         │                                       │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  server.py — asyncio WebSocket server                     │   │
│  │                                                          │   │
│  │  on "start" ──► AudioRecorder.start()                    │   │
│  │  on "stop"  ──► AudioRecorder.stop()                     │   │
│  │              ──► WhisperTranscriber.transcribe()          │   │
│  │              ──► latex_processor.process()                │   │
│  │              ──► send result back via WS                  │   │
│  │  on "cancel"──► AudioRecorder.stop(), discard             │   │
│  └──────────┬──────────────┬──────────────┬─────────────────┘   │
│             │              │              │                      │
│             ▼              ▼              ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐       │
│  │  audio.py     │ │transcriber.py│ │latex_processor.py   │      │
│  │              │ │              │ │                    │       │
│  │  sounddevice  │ │ faster-      │ │ Checks file_type   │      │
│  │  InputStream  │ │ whisper      │ │ If .tex: send to   │      │
│  │  16kHz mono   │ │ small/int8   │ │ Ollama for LaTeX   │      │
│  │  float32      │ │ CPU-only     │ │ conversion         │      │
│  │              │ │              │ │ Else: passthrough   │      │
│  └──────────────┘ └──────────────┘ └─────────┬──────────┘       │
│                                              │                  │
│                                    ┌─────────▼──────────┐       │
│                                    │ ollama_client.py    │       │
│                                    │                    │       │
│                                    │ ollama.chat()       │       │
│                                    │ mistral model       │       │
│                                    └────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: A Complete Dictation

Here is exactly what happens when you press Ctrl+Alt+D, speak, and press Ctrl+Alt+D again:

### 1. Start Recording

```
User presses Ctrl+Alt+D
    │
    ▼
extension.ts: toggle()
    │  state == "ready", so begin recording
    │  Reads the current file extension (e.g. ".tex")
    │
    ▼
extension.ts: send({ command: "start", file_type: ".tex" })
    │  Sends JSON over WebSocket
    │
    ▼
server.py: handle_client() receives message
    │  Parses command: "start"
    │  Stores file_type in active_file_type
    │  Creates AudioRecorder(sample_rate=16000)
    │  Calls recorder.start()
    │
    ▼
audio.py: AudioRecorder.start()
    │  Opens sounddevice.InputStream (16kHz, mono, float32)
    │  Audio callback pushes chunks into a queue
    │
    ▼
server.py: sends { type: "status", state: "recording" }
    │
    ▼
extension.ts: receives status, updates state to "recording"
    │  Status bar shows "Recording..."
```

### 2. Stop and Transcribe

```
User presses Ctrl+Alt+D again
    │
    ▼
extension.ts: toggle()
    │  state == "recording", so stop
    │
    ▼
extension.ts: send({ command: "stop" })
    │
    ▼
server.py: handle_client() receives "stop"
    │  Calls recorder.stop() → returns numpy float32 array
    │  Sends { type: "status", state: "transcribing" }
    │
    ▼
server.py: runs transcriber.transcribe() in executor (thread pool)
    │  This prevents blocking the asyncio event loop
    │
    ▼
transcriber.py: WhisperTranscriber.transcribe(audio)
    │  Calls self.model.transcribe(audio, language="en", vad_filter=True)
    │  Concatenates all segment texts into a single string
    │  Returns: "the integral from zero to infinity of e to the minus x dx"
    │
    ▼
server.py: runs process_latex() in executor
    │
    ▼
latex_processor.py: process(text, file_type=".tex")
    │  file_type is ".tex" → sends text to Ollama
    │
    ▼
ollama_client.py: generate(prompt=text, system=LATEX_SYSTEM_PROMPT)
    │  Calls ollama.chat(model="mistral", ...)
    │  Returns: "$\\int_0^{\\infty} e^{-x} \\, dx$"
    │
    ▼
server.py: sends { type: "result", text: "$\\int_0^{...}" }
    │         sends { type: "status", state: "ready" }
    │
    ▼
extension.ts: receives "result" message
    │  Calls insertText(text)
    │
    ▼
extension.ts: insertText()
    │  Gets active text editor
    │  editor.edit(eb => eb.insert(editor.selection.active, text))
    │  Text appears at cursor position
```

### 3. Cancel (optional)

```
User presses Escape (or runs Cancel command)
    │
    ▼
extension.ts: cancel()
    │  send({ command: "cancel" })
    │
    ▼
server.py: calls recorder.stop(), discards audio
    │  Sends { type: "status", state: "ready" }
    │  No text is inserted
```

## Component Details

### backend/audio.py — Microphone Capture

**Class:** `AudioRecorder`

Wraps `sounddevice.InputStream` with a callback + queue pattern:

- **Constructor:** takes `sample_rate` (default 16000 Hz)
- **start():** opens a new `InputStream` with a callback that copies each audio chunk into a thread-safe `queue.Queue`
- **stop():** stops the stream, drains the queue, concatenates all chunks into a single 1-D `numpy.float32` array

The callback pattern is required because sounddevice's `InputStream` runs its callback on a separate audio thread. The queue bridges between the audio thread and the main thread safely.

**Why 16kHz mono float32?** This is what Whisper expects. Recording at this format avoids any resampling.

### backend/transcriber.py — Speech-to-Text

**Class:** `WhisperTranscriber`

- **Constructor:** loads the faster-whisper model once. Uses `small` model with `int8` quantization for CPU. The model stays in memory across transcription calls (~500MB RAM).
- **transcribe(audio, language, vad_filter):** runs inference on the audio array. Returns all segment texts joined with spaces.

**Why `small` + `int8`?** The `small` model gives ~5% word error rate (vs ~30% for Vosk). `int8` quantization halves memory usage with negligible accuracy loss. Fits comfortably in 14GB RAM alongside Ollama.

**Why `vad_filter=True`?** Voice Activity Detection filters out silence, reducing processing time and avoiding hallucinated text from quiet segments.

### backend/server.py — WebSocket Server

The central coordinator. Key design decisions:

- **Lazy model loading:** the Whisper model is loaded on first client connection, not at server startup. This means the server starts instantly and only uses RAM when needed.
- **Blocking calls in executors:** `transcribe()` and `process_latex()` are CPU-bound. They run in `asyncio.run_in_executor()` (default thread pool) so they don't block the WebSocket event loop.
- **Graceful shutdown:** listens for SIGINT/SIGTERM and cleanly stops the WebSocket server.
- **Per-connection state:** each WebSocket connection tracks its own `recording` flag and `active_file_type`. The `file_type` sent with `start` is stored and used when `stop` triggers the LaTeX processor.

### backend/latex_processor.py — LaTeX Conversion

A single function `process(text, file_type, model, temperature)`:

1. If `file_type != ".tex"` → returns text unchanged (zero overhead for non-LaTeX files)
2. If `.tex` → sends the transcription to Ollama with a system prompt containing LaTeX conversion examples
3. If Ollama fails or returns empty → falls back to raw text (never crashes)

The system prompt instructs the LLM to only convert math-like phrases and leave prose untouched. This means mixed sentences like "In this section we show that x squared equals y" get partially converted: "In this section we show that $x^2 = y$".

### backend/ollama_client.py — Ollama Wrapper

A single function `generate(prompt, system, model, temperature)`:

- Calls `ollama.chat()` with system and user messages
- Wraps everything in try/except — returns empty string on any error
- This means the rest of the system never crashes due to Ollama being down

### backend/config.py — Configuration

Loads `config.yaml` from the project root. Merges user config on top of hardcoded defaults, so any missing key falls back to a sensible default. The config is loaded once at module level in `server.py`.

### vscode-extension/src/extension.ts — Extension

~230 lines of TypeScript. Key parts:

**State machine:** four states — `disconnected`, `ready`, `recording`, `transcribing`. The status bar reflects the current state with appropriate icons and colors.

**WebSocket client:** connects to `ws://localhost:{port}`. Handles three message types from the server: `status` (update state), `result` (insert text), `error` (show notification).

**Auto-start:** if the WebSocket connection fails and `autoStart` is enabled, the extension spawns `python -m backend.server` as a child process. It monitors the process and offers a "Restart Backend" button if it crashes.

**Reconnection:** on disconnect, schedules reconnection with exponential backoff (1s, 2s, 4s, 8s... capped at 30s). Resets to 1s on successful connection. The `voice-to-cursor.reconnect` command allows manual reconnection.

**Cleanup:** on deactivate, the extension closes the WebSocket, clears timers, and kills the backend process (if it started one).

## WebSocket Protocol

All messages are JSON. The protocol is intentionally simple — no authentication, no binary frames, no multiplexing.

### Client to Server

| Message | Description |
|---------|-------------|
| `{"command": "start", "file_type": ".tex"}` | Begin recording. `file_type` determines whether LaTeX processing is applied later. |
| `{"command": "stop"}` | Stop recording, transcribe, and return result. |
| `{"command": "cancel"}` | Stop recording and discard audio. |

### Server to Client

| Message | Description |
|---------|-------------|
| `{"type": "status", "state": "ready"}` | Server is idle, ready for commands. |
| `{"type": "status", "state": "recording"}` | Microphone is active. |
| `{"type": "status", "state": "transcribing"}` | Audio is being processed. |
| `{"type": "result", "text": "..."}` | Transcription result to insert. |
| `{"type": "error", "message": "..."}` | Something went wrong. |

## Why WebSocket?

The Whisper model takes ~5-10 seconds to load. By keeping the backend as a persistent server:

- The model loads once and stays in memory
- Subsequent dictations start instantly
- The extension can reconnect without reloading the model
- Multiple editor windows could theoretically share one backend

An alternative would be spawning a Python process per dictation, but that would add 5-10s of startup latency every time.

## Threading Model

```
┌─────────────────────────────────────────┐
│  asyncio event loop (main thread)        │
│                                         │
│  Handles: WebSocket messages, JSON      │
│  parsing, state management, sending     │
│  responses                              │
│                                         │
│  Delegates blocking work to:            │
│  ┌───────────────────────────────────┐  │
│  │  Thread pool (run_in_executor)     │  │
│  │                                   │  │
│  │  - transcriber.transcribe()       │  │
│  │  - latex_processor.process()      │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Meanwhile, audio runs on:              │
│  ┌───────────────────────────────────┐  │
│  │  sounddevice audio thread          │  │
│  │                                   │  │
│  │  - Calls _callback() per chunk    │  │
│  │  - Puts data into queue.Queue     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

The asyncio event loop never blocks. Audio capture runs on its own thread (managed by sounddevice/portaudio). CPU-heavy work (Whisper inference, Ollama calls) runs in the default thread pool executor.

## Configuration Flow

```
config.yaml (project root)
    │
    ▼
config.py: load_config()
    │  Reads YAML, merges with DEFAULTS dict
    │  Missing keys fall back to defaults
    │
    ▼
server.py: config = load_config()  (module-level, runs once)
    │
    ├──► config["whisper"]  → passed to WhisperTranscriber constructor
    ├──► config["server"]   → host and port for WebSocket server
    ├──► config["audio"]    → sample_rate for AudioRecorder
    └──► config["ollama"]   → model and temperature for LaTeX processing
```

The extension has its own settings (`voice-to-cursor.port`, `voice-to-cursor.autoStart`) managed through the VS Code settings API. These are independent of `config.yaml`.

## Error Handling Strategy

The system is designed to degrade gracefully rather than crash:

| Failure | Behavior |
|---------|----------|
| Backend not running | Extension shows "disconnected", retries with backoff |
| WebSocket disconnects mid-session | Extension auto-reconnects, status bar updates |
| Backend crashes | Extension offers "Restart Backend" button |
| Ollama not running | LaTeX processing returns raw text (no crash) |
| Ollama returns empty | Falls back to raw transcription |
| No microphone | sounddevice raises error, server sends error message |
| Invalid JSON from client | Server sends error message, continues listening |
| No active editor on result | Extension shows warning notification |
