# Vosk Speech-to-Text Pro

Offline speech-to-text transcription system with AI-powered correction and multi-format export.

## Features

- **Three Operating Modes**
  - Transcribe Only: Speech recognition with Vosk (6-8GB RAM)
  - Correct Only: AI correction with Ollama (4-5GB RAM)
  - Full Workflow: Sequential processing optimized for memory usage

- **Multi-Format Export**
  - Plain text, Markdown, HTML, JSON
  - SRT subtitles, PDF, Microsoft Word

- **Performance Optimizations**
  - Intelligent file and correction caching
  - Memory-efficient sequential model loading
  - Progress indicators for long operations

- **File Management**
  - Search across all transcriptions
  - Merge multiple files
  - View statistics and metadata

- **User Interface**
  - Keyboard shortcuts for common actions
  - Settings and diagnostics tools
  - Complete options reference

## Requirements

- Python 3.8 or higher
- Linux (tested on Manjaro/Arch)
- 8GB RAM minimum (16GB recommended)
- Microphone

## Installation

### Quick Start

```bash
git clone https://github.com/ApostolosTsabodimos/vosk-stt-pro.git
cd vosk-stt-pro
./setup.sh
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/ApostolosTsabodimos/vosk-stt-pro.git
cd vosk-stt-pro

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Arch/Manjaro)
sudo pacman -S portaudio ollama

# Download Vosk model
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip
unzip vosk-model-en-us-0.42-gigaspeech.zip
rm vosk-model-en-us-0.42-gigaspeech.zip

# Install Ollama model
ollama pull mistral
```

### Optional: Add Swap Space

If you have less than 8GB of free RAM:

```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Usage

### Starting the Application

```bash
source venv/bin/activate
python vosk_stt.py
```

### Basic Workflow

1. Select operating mode (1-3)
2. For transcription: speak into microphone, press Ctrl+C to finish
3. Choose export format(s) if desired
4. Files are saved to `~/vosk_transcriptions/`

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| T | Transcribe Only mode |
| C | Correct Only mode |
| F | Full Workflow mode |
| O | File Operations |
| S | Settings and Tools |
| H | Help |
| Q | Quit |

## Configuration

Edit `config.yaml` to customize:

- Vosk model path and audio settings
- Output folder and default format
- AI model and correction parameters
- Auto-save interval
- Logging level

## Project Structure

```
vosk-stt-pro/
├── vosk_stt.py           # Main entry point
├── config.yaml           # Configuration
├── requirements.txt      # Python dependencies
├── setup.sh             # Automated setup script
├── src/
│   ├── transcription.py # Vosk integration
│   ├── correction.py    # AI correction
│   ├── ollama_manager.py # Ollama interface
│   ├── file_manager.py  # File operations
│   ├── cache_manager.py # Caching system
│   ├── export_formats.py # Export handlers
│   ├── ui_modes.py      # Operating modes
│   └── ...              # Additional modules
└── logs/                # Application logs
```

## Export Formats

- **TXT**: Plain text
- **Markdown**: Formatted with headers and paragraphs
- **HTML**: Styled web page
- **JSON**: Structured data with metadata
- **SRT**: Subtitle format for video
- **PDF**: Requires `reportlab` package
- **DOCX**: Requires `python-docx` package

Install optional dependencies:

```bash
pip install reportlab python-docx
```

## Troubleshooting

### Model Loading Fails

Check that the model path in `config.yaml` matches the extracted folder name:

```bash
ls vosk-model-en-us-0.42-gigaspeech/
```

### Out of Memory

Add swap space or use a smaller Vosk model. Edit `config.yaml`:

```yaml
vosk:
  model_path: "vosk-model-en-us-0.22"
```

Download the smaller model:

```bash
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

### Ollama Not Found

```bash
sudo pacman -S ollama
sudo systemctl start ollama
ollama pull mistral
```

### Microphone Issues

```bash
# List microphones
arecord -l

# Test recording
arecord -d 3 test.wav
aplay test.wav

# Adjust levels
alsamixer
```

## Performance

- Startup: 2-3 seconds
- Model loading: 1-2 minutes (first time)
- Transcription: Real-time
- Correction: 5-15 seconds per file
- Cache hit rate: 60-80% after initial use

Memory usage by mode:
- Mode 1 (Transcribe): 6-8GB
- Mode 2 (Correct): 4-5GB  
- Mode 3 (Full): 6-8GB peak (sequential loading)

## Acknowledgments

- Vosk: https://alphacephei.com/vosk/
- Ollama: https://ollama.ai/
- Mistral AI: https://mistral.ai/

## Support

- Issues: https://github.com/ApostolosTsabodimos/vosk-stt-pro/issues
- Documentation: See README and inline help (press H in application)

## Version

Current version: 1.0.0
# Vosk-first-project
# Vosk-first-project
