"""WebSocket server — entry point for the backend."""

import asyncio
import json
import signal
from typing import Any

import websockets
from websockets.asyncio.server import Server, ServerConnection

from backend.audio import AudioRecorder
from backend.config import load_config
from backend.latex_processor import process as process_latex
from backend.transcriber import WhisperTranscriber

config = load_config()
transcriber: WhisperTranscriber | None = None
recorder: AudioRecorder | None = None


async def send_json(ws: ServerConnection, data: dict[str, Any]) -> None:
    await ws.send(json.dumps(data))


async def handle_client(ws: ServerConnection) -> None:
    global transcriber, recorder

    if transcriber is None:
        transcriber = WhisperTranscriber(
            model_size=config["whisper"]["model"],
            compute_type=config["whisper"]["compute_type"],
        )

    print(f"[server] Client connected: {ws.remote_address}")
    await send_json(ws, {"type": "status", "state": "ready"})

    recording = False
    active_file_type = ""

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await send_json(ws, {"type": "error", "message": "Invalid JSON"})
                continue

            command = msg.get("command")

            if command == "start":
                if recording:
                    await send_json(ws, {"type": "error", "message": "Already recording"})
                    continue
                file_type = msg.get("file_type", "")
                active_file_type = file_type
                recorder = AudioRecorder(sample_rate=config["audio"]["sample_rate"])
                recorder.start()
                recording = True
                print(f"[server] Recording started (file_type={file_type})")
                await send_json(ws, {"type": "status", "state": "recording"})

            elif command == "stop":
                if not recording or recorder is None:
                    await send_json(ws, {"type": "error", "message": "Not recording"})
                    continue
                audio = recorder.stop()
                recording = False
                print(f"[server] Recording stopped, {len(audio)} samples")

                await send_json(ws, {"type": "status", "state": "transcribing"})

                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    transcriber.transcribe,
                    audio,
                    config["whisper"]["language"],
                    config["whisper"]["vad_filter"],
                )

                print(f"[server] Transcription: {text[:80]}...")

                # LaTeX post-processing for .tex files
                text = await loop.run_in_executor(
                    None,
                    process_latex,
                    text,
                    active_file_type,
                    config["ollama"]["model"],
                    config["ollama"]["temperature"],
                )

                await send_json(ws, {"type": "result", "text": text})
                await send_json(ws, {"type": "status", "state": "ready"})

            elif command == "cancel":
                if recording and recorder is not None:
                    recorder.stop()
                    recording = False
                    print("[server] Recording cancelled")
                await send_json(ws, {"type": "status", "state": "ready"})

            else:
                await send_json(ws, {"type": "error", "message": f"Unknown command: {command}"})

    except websockets.ConnectionClosed:
        print(f"[server] Client disconnected: {ws.remote_address}")
    finally:
        if recording and recorder is not None:
            recorder.stop()


async def main() -> None:
    host = config["server"]["host"]
    port = config["server"]["port"]

    stop = asyncio.get_event_loop().create_future()

    def on_signal() -> None:
        if not stop.done():
            stop.set_result(None)

    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, on_signal)

    async with websockets.serve(handle_client, host, port) as server:
        print(f"[server] Listening on ws://{host}:{port}")
        await stop

    print("[server] Shut down.")


if __name__ == "__main__":
    asyncio.run(main())
