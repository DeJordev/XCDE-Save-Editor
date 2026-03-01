"""Characters tab — editable table of party member stats, split into named groups."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
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
    CHAR_GROUPS_FC,
    CHAR_GROUPS_MAIN,
    MAX_AP,
    MAX_EXP,
    MAX_LEVEL,
    Character,
)
from xcde_editor.core.types import PartyMember, SaveData, SaveKind
from xcde_editor.logging_config import get_logger

log = get_logger("ui.character_tab")

_COLUMNS = ["ID", "Character", "Level", "EXP", "AP"]
_COL_ID = 0
_COL_NAME = 1
_COL_LEVEL = 2
_COL_EXP = 3
_COL_AP = 4

_HEADER_BG = QColor("#2d4a6e")
_HEADER_FG = QColor("#c8d8f0")


class CharacterTab(QWidget):
    """
    Displays all party members in labelled groups, with an edit panel below.

    Groups differ between main-game and Future Connected saves:
      - Main game: Main Party / Guest·Temporary / Future Connected
      - FC:        FC Party / Guest·Crossover / Main Game Characters

    Signals:
        data_changed: emitted whenever the user edits any field.
    """

    data_changed: pyqtSignal = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._save: SaveData | None = None
        self._updating = False
        # Maps table row → index into save.party (header rows are absent from the map)
        self._row_to_party: dict[int, int] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # --- Table ---
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)  # managed manually
        vhdr = self._table.verticalHeader()
        assert vhdr is not None
        vhdr.setVisible(False)
        hdr = self._table.horizontalHeader()
        assert hdr is not None
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(_COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # --- Edit panel ---
        edit_box = QGroupBox("Edit selected character")
        edit_layout = QHBoxLayout(edit_box)
        edit_layout.setSpacing(12)

        self._lbl_char = QLabel("—")
        self._lbl_char.setMinimumWidth(110)
        edit_layout.addWidget(self._lbl_char)

        for label, attr, min_val, max_val in [
            ("Level", "_spin_level", 1, MAX_LEVEL),
            ("EXP", "_spin_exp", 0, MAX_EXP),
            ("AP", "_spin_ap", 0, MAX_AP),
        ]:
            edit_layout.addWidget(QLabel(f"{label}:"))
            spin = QSpinBox()
            spin.setRange(min_val, max_val)
            spin.setGroupSeparatorShown(True)
            spin.setFixedWidth(130)
            spin.valueChanged.connect(self._on_spin_changed)
            setattr(self, attr, spin)
            edit_layout.addWidget(spin)

        edit_layout.addStretch()
        layout.addWidget(edit_box)

        # --- Bulk actions ---
        bulk_box = QGroupBox("Bulk actions")
        bulk_layout = QHBoxLayout(bulk_box)

        bulk_layout.addWidget(QLabel("Set ALL to level:"))
        self._bulk_level = QSpinBox()
        self._bulk_level.setRange(1, MAX_LEVEL)
        self._bulk_level.setValue(MAX_LEVEL)
        self._bulk_level.setFixedWidth(70)
        bulk_layout.addWidget(self._bulk_level)

        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self._on_bulk_level)
        bulk_layout.addWidget(apply_btn)
        bulk_layout.addStretch()

        layout.addWidget(bulk_box)

        self._set_edit_panel_enabled(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_save(self, save: SaveData) -> None:
        self._save = save
        self._populate_table()
        self._set_edit_panel_enabled(False)
        self._lbl_char.setText("—")

    def clear(self) -> None:
        self._save = None
        self._table.setRowCount(0)
        self._row_to_party.clear()
        self._set_edit_panel_enabled(False)

    # ------------------------------------------------------------------
    # Internal — table population
    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        if self._save is None:
            return

        self._updating = True
        self._table.setRowCount(0)
        self._row_to_party.clear()

        # Build lookup: character_id → index in save.party
        cid_to_idx: dict[int, int] = {m.character_id: i for i, m in enumerate(self._save.party)}

        groups = (
            CHAR_GROUPS_FC if self._save.kind is SaveKind.FUTURE_CONNECTED else CHAR_GROUPS_MAIN
        )

        for section_label, char_ids in groups:
            # Only insert the section if at least one character is present
            members_in_section = [(cid, cid_to_idx[cid]) for cid in char_ids if cid in cid_to_idx]
            if not members_in_section:
                continue

            self._insert_header_row(section_label)
            for _cid, idx in members_in_section:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._row_to_party[row] = idx
                self._fill_row(row, self._save.party[idx])

        self._updating = False

    def _insert_header_row(self, label: str) -> None:
        """Insert a full-width, non-selectable section header."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        item = QTableWidgetItem(f"  {label}")
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(_HEADER_BG)
        item.setForeground(_HEADER_FG)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # visible but not selectable
        self._table.setItem(row, 0, item)
        self._table.setSpan(row, 0, 1, len(_COLUMNS))

    def _fill_row(self, row: int, member: PartyMember) -> None:
        try:
            name = Character(member.character_id).name
        except ValueError:
            name = f"ID:{member.character_id}"

        for col, text in enumerate(
            [
                str(member.character_id),
                name,
                str(member.level),
                f"{member.exp:,}",
                f"{member.ap:,}",
            ]
        ):
            item = QTableWidgetItem(text)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
                if col != _COL_NAME
                else Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            )
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, col, item)

    def _refresh_row(self, row: int, member: PartyMember) -> None:
        self._fill_row(row, member)

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
        idx = self._row_to_party.get(row)
        if idx is None:
            # User clicked a header row — deselect and clear edit panel
            self._table.clearSelection()
            self._set_edit_panel_enabled(False)
            return

        member = self._save.party[idx]
        try:
            name = Character(member.character_id).name
        except ValueError:
            name = f"ID:{member.character_id}"

        self._updating = True
        self._lbl_char.setText(f"<b>{name}</b>")
        self._spin_level.setValue(member.level)  # type: ignore[attr-defined]
        self._spin_exp.setValue(member.exp)  # type: ignore[attr-defined]
        self._spin_ap.setValue(member.ap)  # type: ignore[attr-defined]
        self._updating = False

        self._set_edit_panel_enabled(True)

    def _on_spin_changed(self) -> None:
        if self._updating or self._save is None:
            return
        selection = self._table.selectionModel()
        rows = selection.selectedRows() if selection is not None else []
        if not rows:
            return

        row = rows[0].row()
        idx = self._row_to_party.get(row)
        if idx is None:
            return

        member = self._save.party[idx]

        from xcde_editor.core.writer import set_member_ap, set_member_exp, set_member_level

        try:
            set_member_level(member, self._spin_level.value())  # type: ignore[attr-defined]
            set_member_exp(member, self._spin_exp.value())  # type: ignore[attr-defined]
            set_member_ap(member, self._spin_ap.value())  # type: ignore[attr-defined]
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid value", str(exc))
            return

        self._refresh_row(row, member)
        self.data_changed.emit()
        log.debug(
            "Edited party[%d] (ID %d): level=%d exp=%d ap=%d",
            idx,
            member.character_id,
            member.level,
            member.exp,
            member.ap,
        )

    def _on_bulk_level(self) -> None:
        if self._save is None:
            return
        value = self._bulk_level.value()
        from xcde_editor.core.writer import set_member_level

        for member in self._save.party:
            try:
                set_member_level(member, value)
            except ValueError as exc:
                log.warning("Bulk level skipped for ID %d: %s", member.character_id, exc)

        self._populate_table()
        self.data_changed.emit()
        log.info("Bulk level set to %d for all characters.", value)

    def _set_edit_panel_enabled(self, enabled: bool) -> None:
        for attr in ("_spin_level", "_spin_exp", "_spin_ap"):
            spin: QSpinBox = getattr(self, attr)
            spin.setEnabled(enabled)
