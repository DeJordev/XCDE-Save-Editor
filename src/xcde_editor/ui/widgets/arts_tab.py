"""Arts tab — 188-art grid with level and max-unlock tier editing."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from xcde_editor.core.constants import (
    MAX_ART_LEVEL,
    MAX_ART_UNLOCK,
    ArtsLevelUnlocked,
)
from xcde_editor.core.types import ArtEntry, SaveData
from xcde_editor.logging_config import get_logger

log = get_logger("ui.arts_tab")

_COLUMNS = ["#", "Level", "Max unlock"]
_COL_IDX = 0
_COL_LEVEL = 1
_COL_UNLOCK = 2

_UNLOCK_LABELS = {
    0: "0 — IV Beginner (max 4)",
    1: "1 — VII Intermediate (max 7)",
    2: "2 — X Expert (max 10)",
    3: "3 — XII Master (max 12)",
}


class ArtsTab(QWidget):
    """
    Table of all 188 arts with per-row editing and bulk-set actions.

    Signals:
        data_changed: emitted on any edit.
    """

    data_changed: pyqtSignal = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._save: SaveData | None = None
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # --- Notice for FC saves ---
        self._fc_notice = QLabel(
            "<i>Arts data is not available for Future Connected saves (bfsmeria).</i>"
        )
        self._fc_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fc_notice.setVisible(False)
        layout.addWidget(self._fc_notice)

        # --- Table ---
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        vhdr = self._table.verticalHeader()
        assert vhdr is not None
        vhdr.setVisible(False)
        hdr = self._table.horizontalHeader()
        assert hdr is not None
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(_COL_IDX, QHeaderView.ResizeMode.ResizeToContents)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # --- Edit panel ---
        edit_box = QGroupBox("Edit selected art")
        edit_layout = QHBoxLayout(edit_box)

        edit_layout.addWidget(QLabel("Level (0-12):"))
        self._spin_level = QSpinBox()
        self._spin_level.setRange(0, MAX_ART_LEVEL)
        self._spin_level.setFixedWidth(70)
        self._spin_level.valueChanged.connect(self._on_level_changed)
        edit_layout.addWidget(self._spin_level)

        edit_layout.addSpacing(16)
        edit_layout.addWidget(QLabel("Max unlock:"))
        self._combo_unlock = QComboBox()
        for k, v in _UNLOCK_LABELS.items():
            self._combo_unlock.addItem(v, userData=k)
        self._combo_unlock.setFixedWidth(230)
        self._combo_unlock.currentIndexChanged.connect(self._on_unlock_changed)
        edit_layout.addWidget(self._combo_unlock)

        edit_layout.addStretch()
        layout.addWidget(edit_box)

        # --- Bulk actions ---
        bulk_box = QGroupBox("Bulk actions")
        bulk_layout = QHBoxLayout(bulk_box)

        bulk_layout.addWidget(QLabel("Set ALL levels to:"))
        self._bulk_level = QSpinBox()
        self._bulk_level.setRange(0, MAX_ART_LEVEL)
        self._bulk_level.setValue(MAX_ART_LEVEL)
        self._bulk_level.setFixedWidth(60)
        bulk_layout.addWidget(self._bulk_level)
        btn_level = QPushButton("Apply")
        btn_level.setFixedWidth(70)
        btn_level.clicked.connect(self._on_bulk_level)
        bulk_layout.addWidget(btn_level)

        bulk_layout.addSpacing(24)
        bulk_layout.addWidget(QLabel("Set ALL max unlock to:"))
        self._bulk_unlock = QComboBox()
        for k, v in _UNLOCK_LABELS.items():
            self._bulk_unlock.addItem(v, userData=k)
        self._bulk_unlock.setCurrentIndex(MAX_ART_UNLOCK)
        self._bulk_unlock.setFixedWidth(230)
        bulk_layout.addWidget(self._bulk_unlock)
        btn_unlock = QPushButton("Apply")
        btn_unlock.setFixedWidth(70)
        btn_unlock.clicked.connect(self._on_bulk_unlock)
        bulk_layout.addWidget(btn_unlock)

        bulk_layout.addStretch()
        layout.addWidget(bulk_box)

        self._set_edit_panel_enabled(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_save(self, save: SaveData) -> None:
        self._save = save
        # bfsgame and bfsmeria share the same layout — arts are always available.
        self._fc_notice.setVisible(False)
        self._table.setVisible(True)
        self._populate_table()
        self._set_edit_panel_enabled(False)

    def clear(self) -> None:
        self._save = None
        self._table.setRowCount(0)
        self._set_edit_panel_enabled(False)

    # ------------------------------------------------------------------
    # Internal — table
    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        if self._save is None:
            return
        self._updating = True
        self._table.setRowCount(0)
        for art in self._save.arts:
            self._append_art_row(art)
        self._updating = False

    def _append_art_row(self, art: ArtEntry) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._set_row(row, art)

    def _set_row(self, row: int, art: ArtEntry) -> None:
        try:
            unlock_label = ArtsLevelUnlocked(art.max_unlock).name
        except ValueError:
            unlock_label = str(art.max_unlock)

        for col, text in enumerate(
            [
                str(art.index),
                str(art.level),
                f"{art.max_unlock} — {unlock_label}",
            ]
        ):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, col, item)

    def _refresh_row(self, row: int) -> None:
        if self._save is None:
            return
        self._set_row(row, self._save.arts[row])

    # ------------------------------------------------------------------
    # Internal — edit panel
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        selection = self._table.selectionModel()
        rows = selection.selectedRows() if selection is not None else []
        if not rows or self._save is None:
            self._set_edit_panel_enabled(False)
            return

        row = rows[0].row()
        art = self._save.arts[row]

        self._updating = True
        self._spin_level.setValue(art.level)
        self._combo_unlock.setCurrentIndex(art.max_unlock)
        self._updating = False

        self._set_edit_panel_enabled(True)

    def _on_level_changed(self, value: int) -> None:
        if self._updating or self._save is None:
            return
        selection = self._table.selectionModel()
        rows = selection.selectedRows() if selection is not None else []
        if not rows:
            return
        row = rows[0].row()
        art = self._save.arts[row]

        from xcde_editor.core.writer import set_art_level

        try:
            set_art_level(art, value)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid value", str(exc))
            return

        self._refresh_row(row)
        self.data_changed.emit()

    def _on_unlock_changed(self, index: int) -> None:
        if self._updating or self._save is None:
            return
        selection = self._table.selectionModel()
        rows = selection.selectedRows() if selection is not None else []
        if not rows:
            return
        row = rows[0].row()
        art = self._save.arts[row]
        value = self._combo_unlock.itemData(index)

        from xcde_editor.core.writer import set_art_max_unlock

        try:
            set_art_max_unlock(art, value)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid value", str(exc))
            return

        self._refresh_row(row)
        self.data_changed.emit()

    def _on_bulk_level(self) -> None:
        if self._save is None:
            return
        value = self._bulk_level.value()
        from xcde_editor.core.writer import set_art_level

        for art in self._save.arts:
            set_art_level(art, value)
        self._populate_table()
        self.data_changed.emit()
        log.info("Bulk art level set to %d.", value)

    def _on_bulk_unlock(self) -> None:
        if self._save is None:
            return
        value = self._bulk_unlock.currentData()
        from xcde_editor.core.writer import set_art_max_unlock

        for art in self._save.arts:
            set_art_max_unlock(art, value)
        self._populate_table()
        self.data_changed.emit()
        log.info("Bulk art max unlock set to %d.", value)

    def _set_edit_panel_enabled(self, enabled: bool) -> None:
        self._spin_level.setEnabled(enabled)
        self._combo_unlock.setEnabled(enabled)
