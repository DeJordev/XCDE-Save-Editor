"""Tests for core/writer.py — round-trip and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from xcde_editor.core.parser import load_save
from xcde_editor.core.writer import (
    commit_save,
    set_art_level,
    set_art_max_unlock,
    set_member_ap,
    set_member_exp,
    set_member_level,
    set_money,
    set_nopon_coins,
)


def test_round_trip_money(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    set_money(save, 99_999_999)
    commit_save(save)

    reloaded = load_save(main_game_save_file)
    assert reloaded.money == 99_999_999


def test_round_trip_nopon_coins(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    set_nopon_coins(save, 999_999)
    commit_save(save)

    reloaded = load_save(main_game_save_file)
    assert reloaded.nopon_coins == 999_999


def test_round_trip_member_stats(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    member = save.party[0]  # SHULK
    set_member_level(member, 99)
    set_member_exp(member, 9_999_999)
    set_member_ap(member, 9_999_999)
    commit_save(save)

    reloaded = load_save(main_game_save_file)
    shulk = reloaded.party[0]
    assert shulk.level == 99
    assert shulk.exp == 9_999_999
    assert shulk.ap == 9_999_999


def test_round_trip_art(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    art = save.arts[0]
    set_art_level(art, 12)
    set_art_max_unlock(art, 3)
    commit_save(save)

    reloaded = load_save(main_game_save_file)
    assert reloaded.arts[0].level == 12
    assert reloaded.arts[0].max_unlock == 3


def test_unknown_bytes_preserved(main_game_save_file: Path) -> None:
    """Editing known fields must not alter the unknown 300 bytes."""
    save_before = load_save(main_game_save_file)
    original_unknown = save_before.party[0].raw_unknown

    set_member_level(save_before.party[0], 99)
    commit_save(save_before)

    save_after = load_save(main_game_save_file)
    assert save_after.party[0].raw_unknown == original_unknown


def test_out_of_range_money_raises(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    with pytest.raises(ValueError, match="Money"):
        set_money(save, 100_000_000)


def test_out_of_range_level_raises(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    with pytest.raises(ValueError, match="Level"):
        set_member_level(save.party[0], 100)


def test_output_path_override(main_game_save_file: Path, tmp_path: Path) -> None:
    save = load_save(main_game_save_file)
    set_money(save, 12_345)
    out = tmp_path / "output.sav"
    commit_save(save, output_path=out)
    assert out.exists()
    # Original file must be unchanged
    original = load_save(main_game_save_file)
    assert original.money == 10_000
