"""Log panel — live, scrollable log viewer with level filter."""

from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from xcde_editor.logging_config import get_logger

log = get_logger("ui.log_panel")

_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "#888888",
    logging.INFO: "#dddddd",
    logging.WARNING: "#f0c060",
    logging.ERROR: "#e06060",
    logging.CRITICAL: "#ff4040",
}

_LEVEL_OPTIONS = [
    ("DEBUG", logging.DEBUG),
    ("INFO", logging.INFO),
    ("WARNING", logging.WARNING),
    ("ERROR", logging.ERROR),
]


class _QtLogHandler(QObject, logging.Handler):
    """Logging handler that emits a Qt signal for each record."""

    record_emitted: pyqtSignal = pyqtSignal(int, str)  # (levelno, formatted_message)

    def __init__(self) -> None:
        QObject.__init__(self)
        logging.Handler.__init__(self)
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s", datefmt="%H:%M:%S"
        )
        self.setFormatter(fmt)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.record_emitted.emit(record.levelno, msg)
        except Exception:
            self.handleError(record)


class LogPanel(QWidget):
    """
    Live log viewer widget.
    Attaches a logging.Handler to the root logger on construction.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._min_level = logging.DEBUG

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Show level ≥"))

        self._level_combo = QComboBox()
        for label, level in _LEVEL_OPTIONS:
            self._level_combo.addItem(label, userData=level)
        self._level_combo.setCurrentIndex(0)
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        toolbar.addWidget(self._level_combo)

        toolbar.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(70)
        clear_btn.clicked.connect(self._on_clear)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # --- Text area ---
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(2000)
        self._text.setFont(self._monospace_font())
        layout.addWidget(self._text, stretch=1)

        # --- Attach handler ---
        self._handler = _QtLogHandler()
        self._handler.setLevel(logging.DEBUG)
        self._handler.record_emitted.connect(self._on_record)
        logging.getLogger().addHandler(self._handler)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_record(self, levelno: int, message: str) -> None:
        if levelno < self._min_level:
            return

        color = _LEVEL_COLORS.get(levelno, "#dddddd")
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n")

        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()

    def _on_level_changed(self, _index: int) -> None:
        self._min_level = self._level_combo.currentData()

    def _on_clear(self) -> None:
        self._text.clear()

    @staticmethod
    def _monospace_font() -> QFont:
        font = QFont("Menlo")
        if not font.exactMatch():
            font = QFont("Consolas")
        if not font.exactMatch():
            font.setFamily("monospace")
        font.setPointSize(11)
        return font
