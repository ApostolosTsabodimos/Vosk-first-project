"""Microphone capture via sounddevice."""

import queue

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Records audio from the default microphone at 16kHz mono float32."""

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
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
            print(f"[audio] {status}")
        self._queue.put(indata.copy())

    def start(self) -> None:
        """Begin recording from the default input device."""
        self._queue = queue.Queue()
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
