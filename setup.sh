#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Voice to Cursor — Setup ==="
echo

# 1. Check system dependencies
echo "[1/5] Checking system dependencies..."

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.11+."
  exit 1
fi

# Prefer python3, fall back to python
PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
  PYTHON_CMD="python"
fi

python_version=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python: $python_version ($PYTHON_CMD)"

if ! command -v node &>/dev/null; then
  echo "ERROR: node not found. Install Node.js 20+."
  exit 1
fi
echo "  Node: $(node --version)"

if ! command -v npm &>/dev/null; then
  echo "ERROR: npm not found."
  exit 1
fi

# Check portaudio (required by sounddevice)
if pkg-config --exists portaudio-2.0 2>/dev/null; then
  echo "  portaudio: OK"
else
  echo "  WARNING: portaudio not found."
  # Detect platform and suggest install command
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v pacman &>/dev/null; then
      echo "    Install with: sudo pacman -S portaudio"
    elif command -v apt-get &>/dev/null; then
      echo "    Install with: sudo apt-get install portaudio19-dev"
    elif command -v dnf &>/dev/null; then
      echo "    Install with: sudo dnf install portaudio-devel"
    else
      echo "    Install portaudio development headers for your distribution."
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "    Install with: brew install portaudio"
  else
    echo "    Install portaudio development headers for your platform."
  fi
fi

# Check Ollama (optional)
if command -v ollama &>/dev/null; then
  echo "  Ollama: installed"
else
  echo "  Ollama: not found (optional — needed for LaTeX post-processing)"
fi

# 2. Python backend
echo
echo "[2/5] Setting up Python backend..."
cd "$SCRIPT_DIR/backend"

if [ ! -d ".venv" ]; then
  $PYTHON_CMD -m venv .venv
  echo "  Created virtual environment"
fi

source .venv/bin/activate
pip install -q -r requirements.txt
echo "  Dependencies installed"

# Quick import test
python -c "from faster_whisper import WhisperModel; print('  faster-whisper: OK')"
python -c "import sounddevice; print('  sounddevice: OK')"
python -c "import websockets; print('  websockets: OK')"

deactivate
cd "$SCRIPT_DIR"

# 3. VS Code extension
echo
echo "[3/5] Setting up VS Code extension..."
cd "$SCRIPT_DIR/vscode-extension"
npm install --silent
npm run compile
echo "  Extension compiled"
cd "$SCRIPT_DIR"

# 4. Download whisper model (first run)
echo
echo "[4/5] Pre-downloading whisper model..."
cd "$SCRIPT_DIR/backend"
source .venv/bin/activate
python -c "
from faster_whisper import WhisperModel
import sys
print('  Downloading/verifying whisper small model...')
model = WhisperModel('small', device='cpu', compute_type='int8')
print('  Model ready')
"
deactivate
cd "$SCRIPT_DIR"

# 5. Summary
echo
echo "[5/5] Setup complete!"
echo
echo "To start the backend:"
echo "  cd backend && source .venv/bin/activate && python -m backend.server"
echo
echo "To use in Code OSS:"
echo "  1. Open the vscode-extension folder in Code OSS"
echo "  2. Press F5 to launch Extension Development Host"
echo "  3. Press Ctrl+Alt+D to toggle dictation"
echo
echo "Or enable autoStart in extension settings to have it start automatically."
