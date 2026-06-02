"""Manual test: record audio for N seconds, transcribe, print result."""

import sys
import time

from backend.audio import AudioRecorder
from backend.transcriber import WhisperTranscriber


def main() -> None:
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    model_size = sys.argv[2] if len(sys.argv) > 2 else "small"

    transcriber = WhisperTranscriber(model_size=model_size)

    recorder = AudioRecorder()
    print(f"\n[test] Recording for {duration} seconds — speak now!")
    recorder.start()
    time.sleep(duration)
    audio = recorder.stop()
    print(f"[test] Captured {len(audio)} samples ({len(audio) / 16000:.1f}s)")

    print("[test] Transcribing...")
    t0 = time.perf_counter()
    text = transcriber.transcribe(audio)
    elapsed = time.perf_counter() - t0
    print(f"[test] Transcription ({elapsed:.1f}s): {text}")


if __name__ == "__main__":
    main()
