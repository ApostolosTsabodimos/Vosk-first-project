"""Tests for LaTeX post-processing."""

from unittest.mock import patch

from backend.latex_processor import process


def test_non_tex_passthrough() -> None:
    """Non-.tex file types return the text unchanged, no Ollama call."""
    with patch("backend.latex_processor.generate") as mock_gen:
        result = process("hello world", ".py")
        assert result == "hello world"
        mock_gen.assert_not_called()


def test_empty_text_passthrough() -> None:
    """Empty/whitespace text returns early, no Ollama call."""
    with patch("backend.latex_processor.generate") as mock_gen:
        result = process("", ".tex")
        assert result == ""
        mock_gen.assert_not_called()

        result = process("   ", ".tex")
        assert result == "   "
        mock_gen.assert_not_called()


def test_tex_file_calls_ollama() -> None:
    """For .tex files with content, Ollama is called and its result returned."""
    with patch("backend.latex_processor.generate", return_value="$x^2$") as mock_gen:
        result = process("x squared", ".tex")
        assert result == "$x^2$"
        mock_gen.assert_called_once()
        # Verify the transcription text was passed as the prompt
        call_args = mock_gen.call_args
        assert call_args.kwargs["prompt"] == "x squared" or call_args.args[0] == "x squared"


def test_ollama_empty_response_falls_back() -> None:
    """If Ollama returns empty string, fall back to the original text."""
    with patch("backend.latex_processor.generate", return_value=""):
        result = process("x squared", ".tex")
        assert result == "x squared"


def test_ollama_whitespace_response_falls_back() -> None:
    """If Ollama returns only whitespace, fall back to the original text."""
    with patch("backend.latex_processor.generate", return_value="   "):
        result = process("x squared", ".tex")
        assert result == "x squared"


def test_custom_model_and_temperature() -> None:
    """Model and temperature are forwarded to generate()."""
    with patch("backend.latex_processor.generate", return_value="$\\alpha$") as mock_gen:
        process("alpha", ".tex", model="llama3", temperature=0.7)
        call_args = mock_gen.call_args
        assert call_args.kwargs.get("model") == "llama3" or (
            len(call_args.args) >= 3 and call_args.args[2] == "llama3"
        )
