"""Tests for config loading."""

from pathlib import Path

import pytest
import yaml

from backend.config import DEFAULTS, load_config


def test_defaults_when_no_file(tmp_path: Path) -> None:
    """Missing config file returns defaults unchanged."""
    config = load_config(tmp_path / "nonexistent.yaml")
    assert config == DEFAULTS


def test_loads_yaml_file(tmp_path: Path) -> None:
    """User config overrides specific fields, keeps defaults for the rest."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump({"whisper": {"model": "tiny", "language": "el"}}))

    config = load_config(cfg_path)
    assert config["whisper"]["model"] == "tiny"
    assert config["whisper"]["language"] == "el"
    # defaults preserved for fields not overridden
    assert config["whisper"]["compute_type"] == "int8"
    assert config["whisper"]["vad_filter"] is True


def test_merge_preserves_other_sections(tmp_path: Path) -> None:
    """Overriding one section doesn't affect others."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump({"server": {"port": 1234}}))

    config = load_config(cfg_path)
    assert config["server"]["port"] == 1234
    assert config["server"]["host"] == "localhost"
    assert config["audio"]["sample_rate"] == 16000


def test_extra_top_level_key(tmp_path: Path) -> None:
    """Unknown top-level keys are kept as-is."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump({"custom": {"foo": "bar"}}))

    config = load_config(cfg_path)
    assert config["custom"] == {"foo": "bar"}
    # defaults still present
    assert "whisper" in config


def test_empty_yaml_file(tmp_path: Path) -> None:
    """An empty YAML file returns defaults."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("")

    config = load_config(cfg_path)
    assert config == DEFAULTS
