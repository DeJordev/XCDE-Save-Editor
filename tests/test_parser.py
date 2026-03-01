"""Tests for core/parser.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from xcde_editor.core.constants import PLAYABLE_CHARACTER_IDS, TOTAL_ARTS
from xcde_editor.core.parser import load_save
from xcde_editor.core.types import SaveKind
from xcde_editor.core.validator import ValidationError


def test_load_main_game_save(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    assert save.kind is SaveKind.MAIN_GAME
    assert save.is_autosave is False
    assert save.money == 10_000
    assert save.nopon_coins == 500
    assert len(save.party) == len(PLAYABLE_CHARACTER_IDS)
    assert len(save.arts) == TOTAL_ARTS


def test_load_main_game_stats(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    for member in save.party:
        assert member.level == 50
        assert member.exp == 100_000
        assert member.ap == 50_000
        assert len(member.raw_unknown) == 300


def test_load_main_game_arts(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    for art in save.arts:
        assert art.level == 6
        assert art.max_unlock == 2


def test_load_fc_save(fc_save_file: Path) -> None:
    # bfsmeria uses the same binary layout as bfsgame — all fields are parsed.
    save = load_save(fc_save_file)
    assert save.kind is SaveKind.FUTURE_CONNECTED
    assert save.money == 50_000
    assert save.nopon_coins == 777
    assert len(save.party) == len(PLAYABLE_CHARACTER_IDS)
    assert len(save.arts) == TOTAL_ARTS


def test_load_autosave_detection(tmp_path: Path, main_game_buffer: bytearray) -> None:
    autosave = tmp_path / "bfsgame01a.sav"
    autosave.write_bytes(main_game_buffer)
    save = load_save(autosave)
    assert save.is_autosave is True
    assert save.kind is SaveKind.MAIN_GAME


def test_load_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_save(Path("/nonexistent/bfsgame01.sav"))


def test_load_wrong_filename_raises(tmp_path: Path, main_game_buffer: bytearray) -> None:
    bad = tmp_path / "save.dat"
    bad.write_bytes(main_game_buffer)
    with pytest.raises(ValidationError):
        load_save(bad)
