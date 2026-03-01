"""Economy tab — money and Nopon Coins."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from xcde_editor.core.constants import MAX_MONEY, MAX_NOPON_COINS
from xcde_editor.core.types import SaveData
from xcde_editor.logging_config import get_logger

log = get_logger("ui.economy_tab")


class EconomyTab(QWidget):
    """
    Editable money and Nopon Coins fields.

    Nopon Coins and Money are only available in main-game saves (bfsgame).
    The tab shows an info notice for Future Connected saves.

    Signals:
        data_changed: emitted when the user edits any field.
    """

    data_changed: pyqtSignal = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._save: SaveData | None = None
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Notice for FC saves ---
        self._fc_notice = QLabel(
            "<i>Economy data is not available for Future Connected saves (bfsmeria).</i>"
        )
        self._fc_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fc_notice.setVisible(False)
        layout.addWidget(self._fc_notice)

        # --- Edit group ---
        self._edit_group = QGroupBox("Economy")
        form = QFormLayout(self._edit_group)
        form.setSpacing(10)

        self._spin_money = QSpinBox()
        self._spin_money.setRange(0, MAX_MONEY)
        self._spin_money.setGroupSeparatorShown(True)
        self._spin_money.setSuffix("  G")
        self._spin_money.setFixedWidth(180)
        self._spin_money.valueChanged.connect(self._on_money_changed)
        form.addRow("Money:", self._spin_money)

        self._spin_nopon = QSpinBox()
        self._spin_nopon.setRange(0, MAX_NOPON_COINS)
        self._spin_nopon.setGroupSeparatorShown(True)
        self._spin_nopon.setFixedWidth(180)
        self._spin_nopon.valueChanged.connect(self._on_nopon_changed)
        form.addRow("Nopon Coins:", self._spin_nopon)

        layout.addWidget(self._edit_group)
        layout.addStretch()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_save(self, save: SaveData) -> None:
        self._save = save
        self._updating = True

        # bfsgame and bfsmeria share the same layout — economy is always available.
        self._fc_notice.setVisible(False)
        self._edit_group.setVisible(True)
        self._spin_money.setValue(save.money)
        self._spin_nopon.setValue(save.nopon_coins)

        self._updating = False

    def clear(self) -> None:
        self._save = None
        self._updating = True
        self._spin_money.setValue(0)
        self._spin_nopon.setValue(0)
        self._edit_group.setVisible(False)
        self._fc_notice.setVisible(False)
        self._updating = False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_money_changed(self, value: int) -> None:
        if self._updating or self._save is None:
            return
        from xcde_editor.core.writer import set_money

        try:
            set_money(self._save, value)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid value", str(exc))
            return
        self.data_changed.emit()
        log.debug("Money set to %d", value)

    def _on_nopon_changed(self, value: int) -> None:
        if self._updating or self._save is None:
            return
        from xcde_editor.core.writer import set_nopon_coins

        try:
            set_nopon_coins(self._save, value)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid value", str(exc))
            return
        self.data_changed.emit()
        log.debug("Nopon coins set to %d", value)
