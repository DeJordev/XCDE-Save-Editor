"""Structured logging setup with rotation and configurable levels."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path.home() / ".xcde_editor" / "logs"
LOG_FILE = LOG_DIR / "xcde_editor.log"
LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 2 * 1024 * 1024  # 2 MB
BACKUP_COUNT = 5


def setup_logging(level: int = logging.DEBUG) -> None:
    """Configure root logger with a rotating file handler and a console handler."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger("xcde_editor").info("Logging initialised — log file: %s", LOG_FILE)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger under the xcde_editor hierarchy."""
    return logging.getLogger(f"xcde_editor.{name}")
