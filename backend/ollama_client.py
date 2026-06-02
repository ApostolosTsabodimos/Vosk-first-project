"""Thin wrapper around the Ollama Python client."""

import ollama


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
    except Exception as e:
        print(f"[ollama] Error: {e}")
        return ""
