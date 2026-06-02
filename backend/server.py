"""WebSocket server — entry point for the backend."""

import asyncio
import json
import logging
import signal
from functools import partial
from typing import Any

import websockets
from websockets.asyncio.server import Server, ServerConnection

from backend.audio import AudioRecorder
from backend.config import load_config
from backend.latex_processor import process as process_latex
from backend.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)

config = load_config()


async def send_json(ws: ServerConnection, data: dict[str, Any]) -> None:
    await ws.send(json.dumps(data))


async def handle_client(ws: ServerConnection, transcriber: WhisperTranscriber) -> None:
    logger.info("Client connected: %s", ws.remote_address)
    await send_json(ws, {"type": "status", "state": "ready"})

    recorder: AudioRecorder | None = None
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
                recorder = AudioRecorder(
                    sample_rate=config["audio"]["sample_rate"],
                    max_duration=config["audio"]["max_duration"],
                )
                recorder.start()
                recording = True
                logger.info("Recording started (file_type=%s)", file_type)
                await send_json(ws, {"type": "status", "state": "recording"})

            elif command == "stop":
                if not recording or recorder is None:
                    await send_json(ws, {"type": "error", "message": "Not recording"})
                    continue
                audio = recorder.stop()
                recorder = None
                recording = False
                logger.info("Recording stopped, %d samples", len(audio))

                await send_json(ws, {"type": "status", "state": "transcribing"})

                loop = asyncio.get_running_loop()
                text = await loop.run_in_executor(
                    None,
                    transcriber.transcribe,
                    audio,
                    config["whisper"]["language"],
                    config["whisper"]["vad_filter"],
                )

                logger.info("Transcription: %s", text[:80])

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
                    recorder = None
                    recording = False
                    logger.info("Recording cancelled")
                await send_json(ws, {"type": "status", "state": "ready"})

            else:
                await send_json(ws, {"type": "error", "message": f"Unknown command: {command}"})

    except websockets.ConnectionClosed:
        logger.info("Client disconnected: %s", ws.remote_address)
    finally:
        if recording and recorder is not None:
            recorder.stop()


async def main() -> None:
    host = config["server"]["host"]
    port = config["server"]["port"]

    transcriber = WhisperTranscriber(
        model_size=config["whisper"]["model"],
        compute_type=config["whisper"]["compute_type"],
    )

    loop = asyncio.get_running_loop()
    stop: asyncio.Future[None] = loop.create_future()

    def on_signal() -> None:
        if not stop.done():
            stop.set_result(None)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, on_signal)

    handler = partial(handle_client, transcriber=transcriber)
    async with websockets.serve(handler, host, port) as server:
        logger.info("Listening on ws://%s:%d", host, port)
        await stop

    logger.info("Shut down.")


if __name__ == "__main__":
    asyncio.run(main())
