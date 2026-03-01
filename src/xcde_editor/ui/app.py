"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from xcde_editor import __version__
from xcde_editor.backup.manager import BackupManager
from xcde_editor.core.parser import load_save
from xcde_editor.core.types import SaveData
from xcde_editor.core.validator import ValidationError
from xcde_editor.core.writer import WriteError, commit_save
from xcde_editor.logging_config import get_logger
from xcde_editor.ui.dialogs.about import AboutDialog
from xcde_editor.ui.dialogs.confirm import ask_confirm
from xcde_editor.ui.widgets.arts_tab import ArtsTab
from xcde_editor.ui.widgets.backup_tab import BackupTab
from xcde_editor.ui.widgets.character_tab import CharacterTab
from xcde_editor.ui.widgets.economy_tab import EconomyTab
from xcde_editor.ui.widgets.log_panel import LogPanel
from xcde_editor.ui.widgets.save_selector import SaveSelectorWidget

log = get_logger("ui.app")

_SETTINGS_FOLDER_KEY = "last_saves_folder"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._save: SaveData | None = None
        self._unsaved = False
        self._backup_manager: BackupManager | None = None
        self._settings = QSettings("xcde-editor", "xcde-save-editor")

        self.setWindowTitle(f"XCDE Save Editor  v{__version__}")
        self.setMinimumSize(900, 620)

        self._build_ui()
        self._build_menu()
        self._restore_last_folder()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # --- Save selector ---
        self._selector = SaveSelectorWidget()
        self._selector.save_selected.connect(self._on_save_selected)
        self._selector.folder_changed.connect(self._on_folder_changed)
        root.addWidget(self._selector)

        # --- Tab widget ---
        self._tabs = QTabWidget()
        root.addWidget(self._tabs, stretch=1)

        self._char_tab = CharacterTab()
        self._char_tab.data_changed.connect(self._on_data_changed)
        self._tabs.addTab(self._char_tab, "Characters")

        self._arts_tab = ArtsTab()
        self._arts_tab.data_changed.connect(self._on_data_changed)
        self._tabs.addTab(self._arts_tab, "Arts")

        self._econ_tab = EconomyTab()
        self._econ_tab.data_changed.connect(self._on_data_changed)
        self._tabs.addTab(self._econ_tab, "Economy")

        self._backup_tab = BackupTab()
        self._backup_tab.restore_requested.connect(self._on_restore_requested)
        self._backup_tab.delete_requested.connect(self._on_delete_backup_requested)
        self._backup_tab.export_requested.connect(self._on_export_backup)
        self._backup_tab.import_requested.connect(self._on_import_backup)
        self._tabs.addTab(self._backup_tab, "Backups")

        self._log_panel = LogPanel()
        self._tabs.addTab(self._log_panel, "Logs")

        # --- Save action bar ---
        save_bar = QWidget()
        save_bar_layout = QHBoxLayout(save_bar)
        save_bar_layout.setContentsMargins(4, 2, 4, 2)
        save_bar_layout.setSpacing(8)

        self._save_status_label = QLabel("No save loaded.")
        save_bar_layout.addWidget(self._save_status_label)
        save_bar_layout.addStretch()

        self._save_btn = QPushButton("Save changes")
        self._save_btn.setFixedWidth(130)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)
        save_bar_layout.addWidget(self._save_btn)

        root.addWidget(save_bar)

        # --- Status bar ---
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("No save loaded.")

    def _build_menu(self) -> None:
        bar = self.menuBar()
        assert bar is not None

        file_menu = bar.addMenu("&File")
        assert file_menu is not None

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = bar.addMenu("&Help")
        assert help_menu is not None
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _restore_last_folder(self) -> None:
        last = self._settings.value(_SETTINGS_FOLDER_KEY, None)
        if last and Path(last).is_dir():
            self._selector.set_folder(Path(last))

    # ------------------------------------------------------------------
    # Slots — save selection
    # ------------------------------------------------------------------

    def _on_folder_changed(self, folder: Path) -> None:
        self._settings.setValue(_SETTINGS_FOLDER_KEY, str(folder))
        self._backup_manager = BackupManager(folder)
        log.info("Saves folder set to: %s", folder)

    def _on_save_selected(self, path: Path) -> None:
        if self._unsaved and not ask_confirm(
            self,
            "Unsaved changes",
            "You have unsaved changes. Discard them and load a different save?",
        ):
            return

        try:
            save = load_save(path)
        except (FileNotFoundError, ValidationError) as exc:
            QMessageBox.critical(self, "Cannot load save", str(exc))
            log.error("Failed to load save %s: %s", path.name, exc)
            return

        self._save = save
        self._unsaved = False
        self._load_all_tabs(save)
        self._update_title()
        self._update_save_button()
        self._status.showMessage(
            f"Loaded: {path.name}  ({save.kind.name}"
            + ("  •  autosave" if save.is_autosave else "")
            + ")"
        )
        log.info("Save loaded: %s", path.name)

    def _load_all_tabs(self, save: SaveData) -> None:
        self._char_tab.load_save(save)
        self._arts_tab.load_save(save)
        self._econ_tab.load_save(save)
        self._refresh_backup_tab()

    def _refresh_backup_tab(self) -> None:
        if self._save and self._backup_manager:
            entries = self._backup_manager.list_backups(self._save.path)
            self._backup_tab.load_entries(entries)

    # ------------------------------------------------------------------
    # Slots — editing
    # ------------------------------------------------------------------

    def _on_data_changed(self) -> None:
        self._unsaved = True
        self._update_title()
        self._update_save_button()

    def _update_save_button(self) -> None:
        if self._save is None:
            self._save_btn.setEnabled(False)
            self._save_btn.setStyleSheet("")
            self._save_status_label.setText("No save loaded.")
            return
        if self._unsaved:
            self._save_btn.setEnabled(True)
            self._save_btn.setStyleSheet(
                "QPushButton { background-color: #2e7d32; color: white;"
                " font-weight: bold; border-radius: 4px; padding: 4px 8px; }"
                "QPushButton:hover { background-color: #388e3c; }"
                "QPushButton:pressed { background-color: #1b5e20; }"
            )
            self._save_status_label.setText("Unsaved changes")
        else:
            self._save_btn.setEnabled(False)
            self._save_btn.setStyleSheet("")
            self._save_status_label.setText("All changes saved.")

    # ------------------------------------------------------------------
    # Slots — save to disk
    # ------------------------------------------------------------------

    def _on_save(self) -> None:
        if self._save is None:
            return

        if not ask_confirm(
            self,
            "Save changes",
            f"Write changes to '{self._save.path.name}'?\n\n"
            "A backup will be created automatically before writing.",
        ):
            return

        self._write_save()

    def _write_save(self) -> bool:
        """Create backup, write save, return True on success."""
        if self._save is None or self._backup_manager is None:
            return False

        # Backup FIRST — always
        try:
            entry = self._backup_manager.create_backup(self._save.path)
            log.info("Backup created before write: %s", entry.path.name)
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", f"Could not create backup:\n{exc}")
            log.error("Backup failed: %s", exc)
            return False

        # Write
        try:
            commit_save(self._save)
        except (WriteError, OSError) as exc:
            QMessageBox.critical(
                self,
                "Write failed",
                f"Failed to write save file:\n{exc}\n\nYour last backup is: {entry.path.name}",
            )
            log.error("Write failed: %s", exc)
            return False

        self._unsaved = False
        self._update_title()
        self._update_save_button()
        self._refresh_backup_tab()
        self._status.showMessage(f"Saved: {self._save.path.name}")
        log.info("Save written successfully: %s", self._save.path.name)
        return True

    # ------------------------------------------------------------------
    # Slots — backup tab actions
    # ------------------------------------------------------------------

    def _on_restore_requested(self, entry_index: int) -> None:
        if self._save is None or self._backup_manager is None:
            return

        entries = self._backup_manager.list_backups(self._save.path)
        if entry_index >= len(entries):
            return
        entry = entries[entry_index]

        if not ask_confirm(
            self,
            "Restore backup",
            f"Restore backup '{entry.display_name}'?\n\n"
            "The current save will be backed up first, then overwritten.",
        ):
            return

        try:
            self._backup_manager.restore_backup(entry, self._save.path)
        except Exception as exc:
            QMessageBox.critical(self, "Restore failed", str(exc))
            log.error("Restore failed: %s", exc)
            return

        # Reload from disk
        try:
            self._save = load_save(self._save.path)
            self._load_all_tabs(self._save)
            self._unsaved = False
            self._update_title()
        except Exception as exc:
            QMessageBox.critical(self, "Reload failed", str(exc))
            return

        self._status.showMessage(f"Restored: {entry.display_name}")
        log.info("Restored backup: %s", entry.path.name)

    def _on_delete_backup_requested(self, entry_index: int) -> None:
        if self._save is None or self._backup_manager is None:
            return

        entries = self._backup_manager.list_backups(self._save.path)
        if entry_index >= len(entries):
            return
        entry = entries[entry_index]

        if not ask_confirm(
            self,
            "Delete backup",
            f"Permanently delete backup '{entry.display_name}'?\nThis cannot be undone.",
        ):
            return

        self._backup_manager.delete_backup(entry)
        self._refresh_backup_tab()
        log.info("Deleted backup: %s", entry.path.name)

    def _on_export_backup(self, entry_index: int) -> None:
        if self._save is None or self._backup_manager is None:
            return

        from PyQt6.QtWidgets import QFileDialog

        entries = self._backup_manager.list_backups(self._save.path)
        if entry_index >= len(entries):
            return
        entry = entries[entry_index]

        dest, _ = QFileDialog.getSaveFileName(
            self, "Export backup", str(Path.home() / entry.path.name), "Save files (*.sav)"
        )
        if dest:
            try:
                self._backup_manager.export_backup(entry, Path(dest))
                self._status.showMessage(f"Exported backup to {dest}")
            except Exception as exc:
                QMessageBox.critical(self, "Export failed", str(exc))

    def _on_import_backup(self) -> None:
        if self._save is None or self._backup_manager is None:
            return

        from PyQt6.QtWidgets import QFileDialog

        src, _ = QFileDialog.getOpenFileName(
            self, "Import backup", str(Path.home()), "Save files (*.sav)"
        )
        if src:
            try:
                self._backup_manager.import_backup(Path(src), self._save.path)
                self._refresh_backup_tab()
                self._status.showMessage("Backup imported.")
            except Exception as exc:
                QMessageBox.critical(self, "Import failed", str(exc))

    # ------------------------------------------------------------------
    # Slots — misc
    # ------------------------------------------------------------------

    def _on_about(self) -> None:
        AboutDialog(self).exec()

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if a0 is None:
            return
        if self._unsaved and not ask_confirm(
            self,
            "Unsaved changes",
            "You have unsaved changes. Quit without saving?",
        ):
            a0.ignore()
            return
        a0.accept()

    def _update_title(self) -> None:
        base = f"XCDE Save Editor  v{__version__}"
        if self._save:
            indicator = " *" if self._unsaved else ""
            self.setWindowTitle(f"{base}  —  {self._save.path.name}{indicator}")
        else:
            self.setWindowTitle(base)
