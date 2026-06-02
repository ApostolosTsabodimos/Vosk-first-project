"""Microphone capture via sounddevice."""

import logging
import queue

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

DEFAULT_MAX_DURATION = 300  # 5 minutes


class AudioRecorder:
    """Records audio from the default microphone at 16kHz mono float32."""

    def __init__(self, sample_rate: int = 16000, max_duration: int = DEFAULT_MAX_DURATION) -> None:
        self.sample_rate = sample_rate
        self.max_duration = max_duration
        self._max_samples = sample_rate * max_duration
        self._sample_count = 0
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            logger.warning("Audio callback status: %s", status)
        if self._sample_count >= self._max_samples:
            logger.warning("Max recording duration (%ds) reached, dropping audio", self.max_duration)
            return
        self._sample_count += frames
        self._queue.put(indata.copy())

    @property
    def duration_exceeded(self) -> bool:
        """True if the recording has hit the max duration limit."""
        return self._sample_count >= self._max_samples

    def start(self) -> None:
        """Begin recording from the default input device."""
        self._queue = queue.Queue()
        self._sample_count = 0
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured audio as a 1-D float32 array."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        chunks: list[np.ndarray] = []
        while not self._queue.empty():
            chunks.append(self._queue.get())

        if not chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(chunks).flatten()
