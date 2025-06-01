"""LitLum - Scientific publication monitoring and analysis application."""

from .config import Config, CONFIG_DIR, CONFIG_PATH, DEFAULT_CONFIG_PATH
from .__main__ import main

__version__ = "0.1.0"

__all__ = [
    'Config',
    'CONFIG_DIR',
    'CONFIG_PATH',
    'DEFAULT_CONFIG_PATH',
    'main'
]
