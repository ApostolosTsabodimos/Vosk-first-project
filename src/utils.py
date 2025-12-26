"""
Utility functions for Vosk Speech-to-Text application.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default.
        
    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Expand paths
    config['output']['folder'] = os.path.expanduser(config['output']['folder'])
    
    return config

def setup_logging() -> logging.Logger:
    """
    Setup application logging with rotation.
    
    Returns:
        Configured logger instance.
    """
    # Create logs directory
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("vosk_stt")
    logger.setLevel(logging.DEBUG)
    
    # File handler with rotation
    log_file = log_dir / "vosk_stt.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings+ to console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def check_available_memory() -> Dict[str, float]:
    """
    Check available system memory.
    
    Returns:
        Dictionary with memory info in GB
    """
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    value = int(parts[1]) / 1024 / 1024  # Convert to GB
                    meminfo[key] = value
        
        return {
            'total': meminfo.get('MemTotal', 0),
            'available': meminfo.get('MemAvailable', 0),
            'free': meminfo.get('MemFree', 0),
            'swap_total': meminfo.get('SwapTotal', 0),
            'swap_free': meminfo.get('SwapFree', 0)
        }
    except Exception:
        return {'total': 0, 'available': 0, 'free': 0, 'swap_total': 0, 'swap_free': 0}

def show_diff(original: str, corrected: str, max_changes: int = 20) -> None:
    """
    Display differences between original and corrected text.
    
    Args:
        original: Original text
        corrected: Corrected text
        max_changes: Maximum number of changes to display
    """
    orig_words = original.split()
    corr_words = corrected.split()
    
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    
    changes = []
    max_len = max(len(orig_words), len(corr_words))
    
    for i in range(max_len):
        orig_word = orig_words[i] if i < len(orig_words) else "[MISSING]"
        corr_word = corr_words[i] if i < len(corr_words) else "[MISSING]"
        
        if orig_word != corr_word:
            changes.append((orig_word, corr_word))
    
    if not changes:
        print("  No changes made - text was already correct!")
    else:
        for i, (orig, corr) in enumerate(changes[:max_changes], 1):
            print(f"  {i}. '{orig}' → '{corr}'")
        
        if len(changes) > max_changes:
            print(f"  ... and {len(changes) - max_changes} more changes")
    
    print("="*60)

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    Get current timestamp in specified format.
    
    Args:
        format_str: strftime format string
        
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_str)

def validate_filename(filename: str) -> str:
    """
    Validate and sanitize filename.
    
    Args:
        filename: Raw filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. ")
    sanitized = "".join(c if c in valid_chars else "_" for c in filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(". ")
    
    # Ensure not empty
    if not sanitized:
        sanitized = f"file_{get_timestamp()}"
    
    return sanitized
