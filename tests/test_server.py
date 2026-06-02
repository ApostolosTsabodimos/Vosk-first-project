"""Tests for the WebSocket server protocol."""

import asyncio
import json
from functools import partial
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import websockets


@pytest.fixture()
def mocks():
    """Create mock transcriber and patch AudioRecorder + process_latex."""
    mock_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = "hello world"

    mock_recorder = MagicMock()
    mock_recorder.stop.return_value = mock_audio

    with (
        patch("backend.server.AudioRecorder", return_value=mock_recorder),
        patch("backend.server.process_latex", side_effect=lambda text, *a, **kw: text),
    ):
        yield {
            "transcriber": mock_transcriber,
            "recorder": mock_recorder,
        }


async def _start_server(mocks, port: int):
    """Start the server on a given port with the mock transcriber."""
    from backend.server import handle_client

    handler = partial(handle_client, transcriber=mocks["transcriber"])
    server = await websockets.serve(handler, "localhost", port)
    return server


async def _recv_json(ws) -> dict:
    raw = await asyncio.wait_for(ws.recv(), timeout=5)
    return json.loads(raw)


@pytest.mark.asyncio
async def test_connect_receives_ready(mocks) -> None:
    """On connection, server sends a ready status."""
    server = await _start_server(mocks, 19870)
    try:
        async with websockets.connect("ws://localhost:19870") as ws:
            msg = await _recv_json(ws)
            assert msg == {"type": "status", "state": "ready"}
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_start_command(mocks) -> None:
    """Start command transitions to recording state."""
    server = await _start_server(mocks, 19871)
    try:
        async with websockets.connect("ws://localhost:19871") as ws:
            await _recv_json(ws)  # ready
            await ws.send(json.dumps({"command": "start", "file_type": ".tex"}))
            msg = await _recv_json(ws)
            assert msg == {"type": "status", "state": "recording"}
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_start_stop_produces_result(mocks) -> None:
    """Start then stop produces a transcription result."""
    server = await _start_server(mocks, 19872)
    try:
        async with websockets.connect("ws://localhost:19872") as ws:
            await _recv_json(ws)  # ready

            await ws.send(json.dumps({"command": "start"}))
            await _recv_json(ws)  # recording

            await ws.send(json.dumps({"command": "stop"}))
            msg = await _recv_json(ws)  # transcribing
            assert msg == {"type": "status", "state": "transcribing"}

            msg = await _recv_json(ws)  # result
            assert msg["type"] == "result"
            assert msg["text"] == "hello world"

            msg = await _recv_json(ws)  # back to ready
            assert msg == {"type": "status", "state": "ready"}
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_cancel_command(mocks) -> None:
    """Cancel during recording discards audio and returns to ready."""
    server = await _start_server(mocks, 19873)
    try:
        async with websockets.connect("ws://localhost:19873") as ws:
            await _recv_json(ws)  # ready

            await ws.send(json.dumps({"command": "start"}))
            await _recv_json(ws)  # recording

            await ws.send(json.dumps({"command": "cancel"}))
            msg = await _recv_json(ws)
            assert msg == {"type": "status", "state": "ready"}
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_unknown_command(mocks) -> None:
    """Unknown command returns an error."""
    server = await _start_server(mocks, 19874)
    try:
        async with websockets.connect("ws://localhost:19874") as ws:
            await _recv_json(ws)  # ready

            await ws.send(json.dumps({"command": "foobar"}))
            msg = await _recv_json(ws)
            assert msg["type"] == "error"
            assert "foobar" in msg["message"]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_invalid_json(mocks) -> None:
    """Non-JSON message returns an error."""
    server = await _start_server(mocks, 19875)
    try:
        async with websockets.connect("ws://localhost:19875") as ws:
            await _recv_json(ws)  # ready

            await ws.send("this is not json{{{")
            msg = await _recv_json(ws)
            assert msg["type"] == "error"
            assert "Invalid JSON" in msg["message"]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_double_start_error(mocks) -> None:
    """Starting recording twice returns an error."""
    server = await _start_server(mocks, 19876)
    try:
        async with websockets.connect("ws://localhost:19876") as ws:
            await _recv_json(ws)  # ready

            await ws.send(json.dumps({"command": "start"}))
            await _recv_json(ws)  # recording

            await ws.send(json.dumps({"command": "start"}))
            msg = await _recv_json(ws)
            assert msg["type"] == "error"
            assert "Already recording" in msg["message"]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_stop_without_start_error(mocks) -> None:
    """Stopping without starting returns an error."""
    server = await _start_server(mocks, 19877)
    try:
        async with websockets.connect("ws://localhost:19877") as ws:
            await _recv_json(ws)  # ready

            await ws.send(json.dumps({"command": "stop"}))
            msg = await _recv_json(ws)
            assert msg["type"] == "error"
            assert "Not recording" in msg["message"]
    finally:
        server.close()
        await server.wait_closed()
