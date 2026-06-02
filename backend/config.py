"""Configuration loading from config.yaml."""

from pathlib import Path
from typing import Any

import yaml

DEFAULTS: dict[str, Any] = {
    "whisper": {
        "model": "small",
        "compute_type": "int8",
        "language": "en",
        "vad_filter": True,
    },
    "server": {
        "host": "localhost",
        "port": 9876,
    },
    "ollama": {
        "model": "mistral",
        "temperature": 0.3,
    },
    "audio": {
        "sample_rate": 16000,
        "max_duration": 300,
    },
}


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load config.yaml from the project root, falling back to defaults."""
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config.yaml"

    config = dict(DEFAULTS)
    if path.exists():
        with open(path) as f:
            user_config = yaml.safe_load(f) or {}
        for section, values in user_config.items():
            if section in config and isinstance(values, dict):
                config[section] = {**config[section], **values}
            else:
                config[section] = values

    return config
