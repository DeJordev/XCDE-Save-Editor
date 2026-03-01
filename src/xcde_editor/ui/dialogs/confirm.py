"""Confirmation dialog for destructive actions."""

from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget


def ask_confirm(parent: QWidget, title: str, message: str) -> bool:
    """
    Show a modal confirmation dialog.

    Returns True if the user clicked Yes, False otherwise.
    """
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,  # default to safe option
    )
    return reply == QMessageBox.StandardButton.Yes
