"""Backup tab — history list with restore, delete, export and import actions."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from xcde_editor.backup.manager import BackupEntry
from xcde_editor.logging_config import get_logger

log = get_logger("ui.backup_tab")


class BackupTab(QWidget):
    """
    Displays the backup history for the currently active save.

    Signals:
        restore_requested(int): index in the current entries list.
        delete_requested(int): index in the current entries list.
        export_requested(int): index in the current entries list.
        import_requested: user wants to import an external file.
    """

    restore_requested: pyqtSignal = pyqtSignal(int)
    delete_requested: pyqtSignal = pyqtSignal(int)
    export_requested: pyqtSignal = pyqtSignal(int)
    import_requested: pyqtSignal = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries: list[BackupEntry] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._count_label = QLabel("No backups yet.")
        layout.addWidget(self._count_label)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setAlternatingRowColors(True)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list, stretch=1)

        btn_layout = QHBoxLayout()

        self._btn_restore = QPushButton("Restore")
        self._btn_restore.setEnabled(False)
        self._btn_restore.setToolTip("Overwrite the active save with this backup")
        self._btn_restore.clicked.connect(self._on_restore)
        btn_layout.addWidget(self._btn_restore)

        self._btn_export = QPushButton("Export…")
        self._btn_export.setEnabled(False)
        self._btn_export.setToolTip("Save a copy of this backup to a chosen location")
        self._btn_export.clicked.connect(self._on_export)
        btn_layout.addWidget(self._btn_export)

        self._btn_delete = QPushButton("Delete")
        self._btn_delete.setEnabled(False)
        self._btn_delete.setToolTip("Permanently delete this backup")
        self._btn_delete.clicked.connect(self._on_delete)
        btn_layout.addWidget(self._btn_delete)

        btn_layout.addStretch()

        self._btn_import = QPushButton("Import backup…")
        self._btn_import.setToolTip("Import an external .sav file as a backup")
        self._btn_import.clicked.connect(self._on_import)
        btn_layout.addWidget(self._btn_import)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_entries(self, entries: list[BackupEntry]) -> None:
        self._entries = entries
        self._list.clear()

        for entry in reversed(entries):  # newest first
            item = QListWidgetItem(entry.display_name)
            self._list.addItem(item)

        count = len(entries)
        if count > 0:
            suffix = " (newest first)"
        else:
            suffix = " - changes are backed up automatically before every save."
        self._count_label.setText(f"{count} backup{'s' if count != 1 else ''}{suffix}")
        self._set_buttons_enabled(False)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _selected_index(self) -> int | None:
        """Return the index into self._entries for the selected row, or None."""
        rows = self._list.selectedIndexes()
        if not rows:
            return None
        # List is reversed (newest first), so invert
        reversed_index = rows[0].row()
        return len(self._entries) - 1 - reversed_index

    def _on_selection_changed(self) -> None:
        self._set_buttons_enabled(bool(self._list.selectedIndexes()))

    def _on_restore(self) -> None:
        idx = self._selected_index()
        if idx is not None:
            self.restore_requested.emit(idx)

    def _on_export(self) -> None:
        idx = self._selected_index()
        if idx is not None:
            self.export_requested.emit(idx)

    def _on_delete(self) -> None:
        idx = self._selected_index()
        if idx is not None:
            self.delete_requested.emit(idx)

    def _on_import(self) -> None:
        self.import_requested.emit()

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._btn_restore.setEnabled(enabled)
        self._btn_export.setEnabled(enabled)
        self._btn_delete.setEnabled(enabled)
