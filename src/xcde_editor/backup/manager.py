"""
Versioned backup manager.

Before every write the caller MUST invoke create_backup(). The manager:
  - Creates a timestamped copy in  <saves_dir>/.xcde_backups/<stem>/
  - Enforces a configurable maximum number of backups per save (oldest pruned first)
  - Provides listing, restoration, export and import of backups
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from xcde_editor.logging_config import get_logger

log = get_logger("backup.manager")

DEFAULT_MAX_BACKUPS = 20
_BACKUP_DIR_NAME = ".xcde_backups"
_TIMESTAMP_FMT = "%Y%m%d_%H%M%S_%f"


@dataclass(frozen=True)
class BackupEntry:
    """Metadata for a single backup file."""

    path: Path
    stem: str  # original save filename without extension
    timestamp: datetime
    version: int  # 1-based sequential number within the stem group

    @property
    def display_name(self) -> str:
        return f"v{self.version}  —  {self.timestamp.strftime('%Y-%m-%d  %H:%M:%S')}"


class BackupManager:
    """Manages versioned backups for a given saves directory."""

    def __init__(self, saves_dir: Path, max_backups: int = DEFAULT_MAX_BACKUPS) -> None:
        self._saves_dir = saves_dir
        self.max_backups = max_backups

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_backup(self, save_path: Path) -> BackupEntry:
        """
        Copy *save_path* to the backup directory with a timestamped name.
        Prunes oldest backups if the limit is exceeded.

        Returns the BackupEntry for the newly created backup.
        """
        backup_dir = self._backup_dir_for(save_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now()
        ts_str = timestamp.strftime(_TIMESTAMP_FMT)
        suffix = save_path.suffix
        dest = backup_dir / f"{ts_str}{suffix}"

        shutil.copy2(save_path, dest)
        log.info("Backup created: %s", dest)

        entry = BackupEntry(
            path=dest,
            stem=save_path.stem,
            timestamp=timestamp,
            version=0,  # will be assigned after listing
        )

        self._prune(save_path)
        # Return with correct version number after pruning
        all_entries = self.list_backups(save_path)
        for e in all_entries:
            if e.path == dest:
                return e

        return entry  # fallback (shouldn't normally reach here)

    def list_backups(self, save_path: Path) -> list[BackupEntry]:
        """Return all backups for *save_path*, oldest first, with 1-based version numbers."""
        backup_dir = self._backup_dir_for(save_path)
        if not backup_dir.exists():
            return []

        suffix = save_path.suffix
        files = sorted(backup_dir.glob(f"*{suffix}"))
        entries: list[BackupEntry] = []
        for i, f in enumerate(files, start=1):
            try:
                ts = datetime.strptime(f.stem, _TIMESTAMP_FMT)
            except ValueError:
                log.warning("Skipping unrecognized backup file: %s", f)
                continue
            entries.append(
                BackupEntry(
                    path=f,
                    stem=save_path.stem,
                    timestamp=ts,
                    version=i,
                )
            )
        return entries

    def restore_backup(self, entry: BackupEntry, save_path: Path) -> None:
        """
        Overwrite *save_path* with the contents of *entry*.
        A backup of the current save is created first.
        """
        log.info("Restoring backup %s → %s", entry.path, save_path)
        # Snapshot the current file before overwriting
        if save_path.exists():
            self.create_backup(save_path)
        shutil.copy2(entry.path, save_path)
        log.info("Restore complete.")

    def delete_backup(self, entry: BackupEntry) -> None:
        """Permanently delete a single backup file."""
        entry.path.unlink(missing_ok=True)
        log.info("Deleted backup: %s", entry.path)

    def export_backup(self, entry: BackupEntry, destination: Path) -> None:
        """Copy *entry* to an arbitrary user-chosen destination."""
        shutil.copy2(entry.path, destination)
        log.info("Exported backup %s → %s", entry.path, destination)

    def import_backup(self, source: Path, save_path: Path) -> BackupEntry:
        """
        Import an external file as a backup for *save_path*.
        Returns the new BackupEntry.
        """
        backup_dir = self._backup_dir_for(save_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now()
        ts_str = timestamp.strftime(_TIMESTAMP_FMT)
        dest = backup_dir / f"{ts_str}{save_path.suffix}"
        shutil.copy2(source, dest)
        log.info("Imported backup %s → %s", source, dest)

        all_entries = self.list_backups(save_path)
        for e in all_entries:
            if e.path == dest:
                return e

        # Fallback construction
        return BackupEntry(path=dest, stem=save_path.stem, timestamp=timestamp, version=0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _backup_dir_for(self, save_path: Path) -> Path:
        return self._saves_dir / _BACKUP_DIR_NAME / save_path.stem

    def _prune(self, save_path: Path) -> None:
        """Remove oldest backups if the count exceeds *max_backups*."""
        entries = self.list_backups(save_path)
        excess = len(entries) - self.max_backups
        if excess <= 0:
            return
        for old in entries[:excess]:
            log.info("Pruning old backup (limit=%d): %s", self.max_backups, old.path)
            old.path.unlink(missing_ok=True)
