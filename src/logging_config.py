"""
Logging configuration.

Provides a single entry point to obtain configured loggers.
"""

from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from src.config import get_logging_config

_logging_configured = False


def configure_logging() -> None:
    """
    Configure root logger once based on config.yaml.
    Safe to call multiple times.
    """
    global _logging_configured
    if _logging_configured:
        return

    cfg = get_logging_config()
    level_name = cfg.get("level", "INFO")
    fmt = cfg.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = cfg.get("file", "finance_tracker.log")

    level = getattr(logging, level_name.upper(), logging.INFO)

    handlers: list[logging.Handler] = []

    file_path = Path(log_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    handlers.append(file_handler)

    stream_handler = logging.StreamHandler()
    handlers.append(stream_handler)

    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=handlers,
        force=True,
    )

    _logging_configured = True


def get_logger(name: str | None = None) -> Logger:
    """
    Return a logger instance with global configuration applied.
    """
    configure_logging()
    return logging.getLogger(name if name else __name__)
