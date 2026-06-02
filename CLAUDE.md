# Voice to Cursor — Project Rules

## Project Overview

Speech-to-text tool that transcribes dictation directly at the cursor position in Code OSS. Primary use case: LaTeX files. Works with any file type.

**Architecture**: Python backend (faster-whisper + sounddevice) ↔ WebSocket (localhost:9876) ↔ Code OSS extension (TypeScript)

## Tech Stack

### Backend (Python 3.13)
- **STT**: faster-whisper (`small` model, `compute_type="int8"`, CPU-only)
- **Audio**: sounddevice (InputStream, 16kHz, float32)
- **IPC**: websockets (asyncio server on port 9876)
- **LaTeX**: Ollama (mistral) for spoken-math → LaTeX conversion
- **Config**: PyYAML

### Extension (TypeScript)
- **Target**: Code OSS / VS Code
- **IPC**: WebSocket client (`ws` library)
- **Keybinding**: Ctrl+Alt+D (toggle recording)

### System
- Manjaro Linux, AMD Ryzen 5 Pro 7535U, 14GB RAM, no GPU
- Python 3.13, Node 26, Code OSS 1.121.0

## Directory Structure

```
vosk-project/
├── legacy/                    # Old Vosk-based code (reference only)
├── backend/
│   ├── server.py              # WebSocket server (entry point)
│   ├── transcriber.py         # faster-whisper wrapper
│   ├── audio.py               # Mic capture via sounddevice
│   ├── latex_processor.py     # LaTeX post-processing via Ollama
│   ├── ollama_client.py       # Ollama thin wrapper
│   ├── config.py              # Config loading
│   └── requirements.txt
├── vscode-extension/
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/extension.ts
│   └── .vscodeignore
├── config.yaml                # Shared config
├── setup.sh                   # Setup script
├── CLAUDE.md                  # This file
└── .agents/                   # AI workflow artifacts
```

## Build & Run Commands

### Backend
```bash
# Setup
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
python -m backend.server

# Test pipeline manually
python backend/test_pipeline.py
```

### Extension
```bash
# Setup
cd vscode-extension && npm install

# Compile
npm run compile

# Test in dev host
# Press F5 in Code OSS with the extension folder open
```

### System Dependencies
```bash
sudo pacman -S portaudio  # Required by sounddevice
```

## Self-Correction Workflow

When writing code, always follow this loop:
1. **Write** the code
2. **Check** — run the relevant linter/type checker:
   - Python: `ruff check backend/` and `python -m py_compile <file>`
   - TypeScript: `npx tsc --noEmit`
3. **Fix** any errors
4. **Repeat** until clean

## WebSocket Protocol

```
Client → Server:  {"command": "start", "file_type": ".tex"}
Client → Server:  {"command": "stop"}
Client → Server:  {"command": "cancel"}
Server → Client:  {"type": "status", "state": "recording|transcribing|ready"}
Server → Client:  {"type": "result", "text": "..."}
Server → Client:  {"type": "error", "message": "..."}
```

## Code Style

### Python
- Use type hints on all function signatures
- Use `async`/`await` for all I/O-bound code in the server
- No classes where a plain function suffices
- Docstrings only on public API

### TypeScript
- Strict mode enabled
- Prefer `const` over `let`
- Use the VS Code API types (`vscode.TextEditor`, etc.)

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| STT engine | faster-whisper `small` + int8 | ~5% WER vs Vosk's 30%; fits in 14GB RAM |
| IPC | WebSocket | Model stays loaded across sessions |
| Audio | sounddevice | Simpler than pyaudio, well-maintained |
| Keybinding | Ctrl+Alt+D | D for Dictation, no conflicts |
| LaTeX | Ollama LLM only | SayTeX is abandoned; LLM handles this |
| Extension | Minimal (~150 LOC) | Logic lives in Python backend |
