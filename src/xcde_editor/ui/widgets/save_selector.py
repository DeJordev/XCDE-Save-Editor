"""Top-bar widget: folder picker + save file dropdown."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from xcde_editor.logging_config import get_logger

log = get_logger("ui.save_selector")

_KNOWN_EXTENSIONS = {".sav"}
_KNOWN_PREFIXES = ("bfsgame", "bfsmeria")


class SaveSelectorWidget(QWidget):
    """
    Lets the user pick a saves folder and select the active save file.

    Signals:
        save_selected(Path): emitted when the user chooses a different save.
        folder_changed(Path): emitted when a new folder is confirmed.
    """

    save_selected: pyqtSignal = pyqtSignal(Path)
    folder_changed: pyqtSignal = pyqtSignal(Path)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._folder: Path | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Saves folder:"))

        self._folder_label = QLabel("(none)")
        self._folder_label.setMinimumWidth(260)
        layout.addWidget(self._folder_label, stretch=1)

        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(browse_btn)

        layout.addWidget(QLabel("Active save:"))

        self._combo = QComboBox()
        self._combo.setMinimumWidth(220)
        self._combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self._combo)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_folder(self, folder: Path) -> None:
        """Programmatically set the saves folder and refresh the dropdown."""
        self._folder = folder
        self._folder_label.setText(str(folder))
        self._refresh_combo()
        self.folder_changed.emit(folder)

    @property
    def current_save(self) -> Path | None:
        """The currently selected save path, or None if no folder is set."""
        idx = self._combo.currentIndex()
        if idx < 0:
            return None
        return self._combo.itemData(idx)

    @property
    def folder(self) -> Path | None:
        return self._folder

    def refresh(self) -> None:
        """Re-scan the folder and update the dropdown."""
        self._refresh_combo()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_browse(self) -> None:
        start = str(self._folder) if self._folder else str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Select saves folder", start)
        if chosen:
            self.set_folder(Path(chosen))

    def _refresh_combo(self) -> None:
        if self._folder is None:
            return

        previous = self.current_save
        self._combo.blockSignals(True)
        self._combo.clear()

        saves = sorted(
            f
            for f in self._folder.iterdir()
            if f.suffix in _KNOWN_EXTENSIONS and f.name.lower().startswith(_KNOWN_PREFIXES)
        )

        for path in saves:
            label = self._label_for(path)
            self._combo.addItem(label, userData=path)

        # Restore previous selection if still present
        if previous is not None:
            for i in range(self._combo.count()):
                if self._combo.itemData(i) == previous:
                    self._combo.setCurrentIndex(i)
                    break

        self._combo.blockSignals(False)

        if self._combo.count() > 0:
            self._emit_current()

        log.debug("Refreshed combo: %d saves in %s", self._combo.count(), self._folder)

    def _on_combo_changed(self, _index: int) -> None:
        self._emit_current()

    def _emit_current(self) -> None:
        path = self.current_save
        if path is not None:
            log.info("Active save changed: %s", path.name)
            self.save_selected.emit(path)

    @staticmethod
    def _label_for(path: Path) -> str:
        name = path.name
        parts: list[str] = [name]
        if name.lower().startswith("bfsmeria"):
            parts.append("[Future Connected]")
        if name.lower().endswith("a.sav"):
            parts.append("[autosave]")
        return "  ".join(parts)
