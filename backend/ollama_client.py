"""Thin wrapper around the Ollama Python client."""

import logging

import ollama

logger = logging.getLogger(__name__)


def generate(prompt: str, system: str, model: str = "mistral", temperature: float = 0.3) -> str:
    """Send a chat completion request to Ollama and return the response text."""
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": temperature},
        )
        return response.message.content or ""
    except (ollama.RequestError, ollama.ResponseError) as e:
        logger.error("Ollama request failed: %s", e)
        return ""
    except ConnectionError as e:
        logger.error("Cannot reach Ollama server: %s", e)
        return ""
