"""
Vosk Speech-to-Text Professional Edition
A modular, maintainable speech-to-text application with AI correction.
"""

__version__ = "2.0.0"
__author__ = "Your Name"

from .transcription import VoskTranscriber
from .correction import CorrectionManager
from file_manager import FileManager
from ollama_manager import OllamaManager
from ui import VoskCLI

__all__ = [
    'VoskTranscriber',
    'CorrectionManager',
    'FileManager',
    'OllamaManager',
    'VoskCLI',
]
