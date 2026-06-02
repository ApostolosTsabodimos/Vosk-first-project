#!/bin/bash
# Automated setup script for Vosk Speech-to-Text Pro

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Vosk Speech-to-Text Pro - Automated Setup               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}✗ This script is designed for Linux systems${NC}"
    exit 1
fi

echo "📋 Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}✗ pip not found. Please install pip${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} pip found"

# Create virtual environment
echo ""
echo "🔧 Setting up virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC} venv already exists, skipping..."
else
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate venv
source venv/bin/activate

# Install Python dependencies
echo ""
echo "📦 Installing Python packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓${NC} Python packages installed"

# Check for system dependencies
echo ""
echo "🔍 Checking system dependencies..."

# PortAudio
if ! ldconfig -p | grep -q libportaudio; then
    echo -e "${YELLOW}⚠${NC} PortAudio not found"
    echo "  Install with: sudo pacman -S portaudio"
else
    echo -e "${GREEN}✓${NC} PortAudio found"
fi

# Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Ollama not found"
    echo "  Install with: sudo pacman -S ollama"
else
    echo -e "${GREEN}✓${NC} Ollama found"
fi

# Check for Vosk model
echo ""
echo "📥 Checking for Vosk model..."
if [ -d "vosk-model-en-us-0.42-gigaspeech" ]; then
    echo -e "${GREEN}✓${NC} Vosk model found"
else
    echo -e "${YELLOW}⚠${NC} Vosk model not found"
    read -p "Download Vosk model (2.3GB)? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Downloading..."
        wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip
        echo "  Extracting..."
        unzip -q vosk-model-en-us-0.42-gigaspeech.zip
        rm vosk-model-en-us-0.42-gigaspeech.zip
        echo -e "${GREEN}✓${NC} Model downloaded and extracted"
    fi
fi

# Check for Ollama model
echo ""
echo "🤖 Checking for Ollama model..."
if ollama list 2>/dev/null | grep -q "mistral"; then
    echo -e "${GREEN}✓${NC} Mistral model found"
else
    echo -e "${YELLOW}⚠${NC} Mistral model not found"
    read -p "Download Mistral model (4GB)? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ollama pull mistral
        echo -e "${GREEN}✓${NC} Mistral model downloaded"
    fi
fi

# Check memory
echo ""
echo "💾 Checking system memory..."
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
AVAIL_MEM=$(free -g | awk '/^Mem:/{print $7}')
SWAP_MEM=$(free -g | awk '/^Swap:/{print $2}')

echo "  Total RAM: ${TOTAL_MEM}GB"
echo "  Available RAM: ${AVAIL_MEM}GB"
echo "  Swap: ${SWAP_MEM}GB"

if [ "$AVAIL_MEM" -lt 6 ] && [ "$SWAP_MEM" -lt 4 ]; then
    echo -e "${YELLOW}⚠${NC} Low memory detected (recommend 8GB+ available)"
    echo "  Consider adding swap space:"
    echo "  sudo fallocate -l 8G /swapfile"
    echo "  sudo chmod 600 /swapfile"
    echo "  sudo mkswap /swapfile"
    echo "  sudo swapon /swapfile"
fi

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p ~/vosk_transcriptions
echo -e "${GREEN}✓${NC} Directories created"

# Test imports
echo ""
echo "🧪 Testing installation..."
python3 << EOF
import sys
try:
    import vosk
    import pyaudio
    import yaml
    import ollama
    print("${GREEN}✓${NC} All imports successful")
    sys.exit(0)
except ImportError as e:
    print(f"${RED}✗${NC} Import error: {e}")
    sys.exit(1)
EOF

# Setup complete
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! 🎉                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "To run the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python vosk_stt.py"
echo ""
echo "Or create an alias in ~/.zshrc:"
echo "  alias vosk='cd $(pwd) && source venv/bin/activate && python vosk_stt.py'"
echo ""
echo "For help, run: python vosk_stt.py and press 'H'"
echo ""
