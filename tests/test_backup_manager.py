"""Tests for backup/manager.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from xcde_editor.backup.manager import BackupManager


@pytest.fixture()
def saves_dir(tmp_path: Path) -> Path:
    d = tmp_path / "saves"
    d.mkdir()
    return d


@pytest.fixture()
def save_file(saves_dir: Path) -> Path:
    f = saves_dir / "bfsgame01.sav"
    f.write_bytes(b"\x00" * 100)
    return f


def test_create_backup_creates_file(saves_dir: Path, save_file: Path) -> None:
    mgr = BackupManager(saves_dir)
    entry = mgr.create_backup(save_file)
    assert entry.path.exists()
    assert entry.version == 1


def test_list_backups_ordered(saves_dir: Path, save_file: Path) -> None:
    mgr = BackupManager(saves_dir)
    mgr.create_backup(save_file)
    mgr.create_backup(save_file)
    mgr.create_backup(save_file)
    entries = mgr.list_backups(save_file)
    assert len(entries) == 3
    versions = [e.version for e in entries]
    assert versions == [1, 2, 3]


def test_prune_respects_limit(saves_dir: Path, save_file: Path) -> None:
    mgr = BackupManager(saves_dir, max_backups=3)
    for _ in range(5):
        mgr.create_backup(save_file)
    entries = mgr.list_backups(save_file)
    assert len(entries) == 3


def test_restore_backup(saves_dir: Path, save_file: Path) -> None:
    original_content = b"\xab" * 100
    save_file.write_bytes(original_content)

    mgr = BackupManager(saves_dir)
    entry = mgr.create_backup(save_file)

    # Corrupt the live save
    save_file.write_bytes(b"\x00" * 100)
    assert save_file.read_bytes() == b"\x00" * 100

    mgr.restore_backup(entry, save_file)
    assert save_file.read_bytes() == original_content


def test_restore_creates_snapshot_first(saves_dir: Path, save_file: Path) -> None:
    mgr = BackupManager(saves_dir)
    entry = mgr.create_backup(save_file)
    # At this point there is 1 backup; restore should create another
    mgr.restore_backup(entry, save_file)
    entries = mgr.list_backups(save_file)
    assert len(entries) >= 2


def test_delete_backup(saves_dir: Path, save_file: Path) -> None:
    mgr = BackupManager(saves_dir)
    entry = mgr.create_backup(save_file)
    mgr.delete_backup(entry)
    assert not entry.path.exists()
    assert mgr.list_backups(save_file) == []


def test_export_backup(saves_dir: Path, save_file: Path, tmp_path: Path) -> None:
    mgr = BackupManager(saves_dir)
    entry = mgr.create_backup(save_file)
    dest = tmp_path / "exported.sav"
    mgr.export_backup(entry, dest)
    assert dest.exists()
    assert dest.read_bytes() == entry.path.read_bytes()


def test_import_backup(saves_dir: Path, save_file: Path, tmp_path: Path) -> None:
    external = tmp_path / "external_backup.sav"
    external.write_bytes(b"\xff" * 100)

    mgr = BackupManager(saves_dir)
    entry = mgr.import_backup(external, save_file)
    assert entry.path.exists()
    assert entry.path.read_bytes() == b"\xff" * 100


def test_no_backups_returns_empty_list(saves_dir: Path, save_file: Path) -> None:
    mgr = BackupManager(saves_dir)
    assert mgr.list_backups(save_file) == []
