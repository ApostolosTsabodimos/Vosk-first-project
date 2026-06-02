"""Faster-whisper transcription wrapper."""

import time

import numpy as np
from faster_whisper import WhisperModel


class WhisperTranscriber:
    """Loads a faster-whisper model once and transcribes audio arrays."""

    def __init__(
        self,
        model_size: str = "small",
        compute_type: str = "int8",
        device: str = "cpu",
    ) -> None:
        self.model_size = model_size
        print(f"[transcriber] Loading whisper model '{model_size}' ({compute_type})...")
        t0 = time.perf_counter()
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        elapsed = time.perf_counter() - t0
        print(f"[transcriber] Model loaded in {elapsed:.1f}s")

    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "en",
        vad_filter: bool = True,
    ) -> str:
        """Transcribe a float32 audio array and return the text."""
        segments, info = self.model.transcribe(
            audio,
            language=language,
            vad_filter=vad_filter,
        )
        text = " ".join(segment.text.strip() for segment in segments)
        return text
