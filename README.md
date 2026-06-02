# Voice to Cursor

Speech-to-text dictation tool for Code OSS (VS Code). Press **Ctrl+Alt+D** to start dictating — your words appear at the cursor. When editing `.tex` files, spoken math is automatically converted to LaTeX commands via a local LLM.

## How It Works

A **Python backend** captures audio from your microphone, transcribes it with [faster-whisper](https://github.com/SYSTRAN/faster-whisper), and optionally post-processes it through [Ollama](https://ollama.com) for LaTeX conversion. A lightweight **Code OSS extension** connects to the backend over WebSocket, sends start/stop commands, and inserts the result at your cursor.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full technical breakdown.

## Requirements

- **Manjaro Linux** (or any Linux with PulseAudio/PipeWire)
- **Python 3.13+**
- **Node.js 20+** and npm
- **portaudio** — `sudo pacman -S portaudio`
- **Ollama** (optional) — only needed for LaTeX math conversion

Hardware: tested on AMD Ryzen 5 Pro 7535U with 14GB RAM, no GPU required.

## Quick Start

### 1. Run the setup script

```bash
git clone https://github.com/ApostolosTsabodimos/Vosk-first-project.git
cd Vosk-first-project
./setup.sh
```

This creates a Python virtual environment, installs all dependencies, compiles the extension, and pre-downloads the Whisper model (~461MB on first run).

### 2. Start the backend

```bash
cd backend
source .venv/bin/activate
python -m backend.server
```

You should see:
```
[transcriber] Loading whisper model 'small' (int8)...
[transcriber] Model loaded in X.Xs
[server] Listening on ws://localhost:9876
```

### 3. Load the extension

1. Open the `vscode-extension/` folder in Code OSS
2. Press **F5** to launch the Extension Development Host
3. Open any file and press **Ctrl+Alt+D** to start dictating
4. Press **Ctrl+Alt+D** again to stop and insert the transcription

The status bar (bottom-right) shows the current state:
- `$(debug-disconnect) Voice` — disconnected from backend
- `$(mic) Voice` — ready, click or press Ctrl+Alt+D to record
- `$(record) Recording...` — listening to your microphone
- `$(loading~spin) Transcribing...` — processing your audio

## Usage

### Basic Dictation (any file type)

1. Place your cursor where you want text
2. Press **Ctrl+Alt+D** — status bar turns to "Recording..."
3. Speak naturally
4. Press **Ctrl+Alt+D** again — text is inserted at cursor

### LaTeX Dictation (.tex files)

When dictating into a `.tex` file, the transcription is routed through Ollama to convert spoken math into LaTeX:

| You say | You get |
|---------|---------|
| "fraction x over y" | `\frac{x}{y}` |
| "x squared plus y squared equals z squared" | `$x^2 + y^2 = z^2$` |
| "the integral from zero to infinity of e to the minus x dx" | `$\int_0^{\infty} e^{-x} \, dx$` |
| "consider the function f of x" | `consider the function $f(x)$` |
| "In this section we prove" | `In this section we prove` (unchanged) |

Requires Ollama running with the `mistral` model:
```bash
ollama pull mistral
ollama serve   # if not already running
```

If Ollama is unavailable, dictation still works — you just get raw text without math conversion.

### Cancel a Recording

Press **Escape** (or run `Voice to Cursor: Cancel Recording` from the command palette) to discard the current recording without inserting anything.

### Reconnect

If the backend disconnects, the extension automatically reconnects with exponential backoff (1s, 2s, 4s... up to 30s). You can also manually reconnect via the command palette: `Voice to Cursor: Reconnect to Backend`.

## Configuration

### config.yaml (backend)

Located at the project root. Controls the Whisper model, server port, and Ollama settings:

```yaml
whisper:
  model: "small"        # Whisper model size: tiny, base, small, medium, large
  compute_type: "int8"  # Quantization: int8, float16, float32
  language: "en"        # Language code
  vad_filter: true      # Voice Activity Detection (filters silence)

server:
  host: "localhost"
  port: 9876

ollama:
  model: "mistral"      # Any Ollama model
  temperature: 0.3      # Lower = more conservative output

audio:
  sample_rate: 16000    # 16kHz (required by Whisper)
```

### Extension Settings (Code OSS)

| Setting | Default | Description |
|---------|---------|-------------|
| `voice-to-cursor.port` | `9876` | WebSocket server port |
| `voice-to-cursor.autoStart` | `true` | Auto-start the Python backend when it's not running |

## Project Structure

```
vosk-project/
├── backend/
│   ├── __init__.py
│   ├── __main__.py           # python -m backend entry point
│   ├── server.py             # WebSocket server (main loop)
│   ├── transcriber.py        # faster-whisper wrapper
│   ├── audio.py              # Microphone capture (sounddevice)
│   ├── latex_processor.py    # Spoken math → LaTeX via Ollama
│   ├── ollama_client.py      # Ollama API wrapper
│   ├── config.py             # Config loader with defaults
│   ├── test_pipeline.py      # Manual test script
│   └── requirements.txt
├── vscode-extension/
│   ├── package.json
│   ├── tsconfig.json
│   ├── .vscodeignore
│   └── src/
│       └── extension.ts      # Extension entry point
├── legacy/                   # Old Vosk-based code (reference)
├── config.yaml               # Shared configuration
├── setup.sh                  # One-command setup
├── ARCHITECTURE.md           # Technical architecture docs
├── CLAUDE.md                 # AI assistant project rules
└── README.md                 # This file
```

## Troubleshooting

**"Cannot connect to backend"**
- Make sure the backend is running: `python -m backend.server`
- Check that port 9876 isn't in use: `ss -tlnp | grep 9876`

**No audio / "input overflow" warnings**
- Check your default input device: `python -c "import sounddevice; print(sounddevice.query_devices())"`
- Make sure your microphone is not muted in PulseAudio/PipeWire

**Model loading is slow**
- First load downloads the model (~461MB). Subsequent starts use the cached model.
- The `small` model takes ~5-10s to load on CPU. Use `tiny` or `base` in `config.yaml` for faster loading (lower accuracy).

**LaTeX conversion not working**
- Check Ollama is running: `ollama list`
- Pull the model: `ollama pull mistral`
- If Ollama is down, dictation still works with raw text

**Extension not activating**
- Make sure you opened the `vscode-extension/` folder (not the project root) in Code OSS
- Press F5 to launch the Extension Development Host
- Check the Output panel (select "Voice to Cursor" from the dropdown)

## License

MIT
