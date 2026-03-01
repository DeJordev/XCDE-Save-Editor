"""Shared fixtures for the XCDE Save Editor test suite."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from xcde_editor.core.constants import (
    AP_OFFSET_IN_MEMBER,
    ARTS_LEVEL_SIZE,
    ARTS_LEVELS_OFFSET,
    EXP_OFFSET_IN_MEMBER,
    LEVEL_OFFSET_IN_MEMBER,
    MIN_SAVE_SIZE,
    MONEY_OFFSET,
    NOPON_COINS_OFFSET,
    PARTY_MEMBER_SIZE,
    PARTY_MEMBERS_OFFSET,
    TOTAL_ARTS,
)


def make_main_game_buffer(
    *,
    level: int = 50,
    exp: int = 100_000,
    ap: int = 50_000,
    money: int = 10_000,
    nopon_coins: int = 500,
) -> bytearray:
    """
    Build a synthetic main-game save buffer large enough to pass validation.
    All bytes are zero except the fields we explicitly set.
    """
    buf = bytearray(MIN_SAVE_SIZE)

    # Money and nopon coins
    struct.pack_into("<I", buf, MONEY_OFFSET, money)
    struct.pack_into("<I", buf, NOPON_COINS_OFFSET, nopon_coins)

    # Set level/exp/ap for every party member slot (15 members)
    for pos in range(15):
        base = PARTY_MEMBERS_OFFSET + pos * PARTY_MEMBER_SIZE
        struct.pack_into("<I", buf, base + LEVEL_OFFSET_IN_MEMBER, level)
        struct.pack_into("<I", buf, base + EXP_OFFSET_IN_MEMBER, exp)
        struct.pack_into("<I", buf, base + AP_OFFSET_IN_MEMBER, ap)

    # Set a plausible art level / max_unlock for every art
    for i in range(TOTAL_ARTS):
        offset = ARTS_LEVELS_OFFSET + i * ARTS_LEVEL_SIZE
        buf[offset] = 6  # level
        buf[offset + 1] = 2  # X_EXPERT

    return buf


@pytest.fixture()
def main_game_buffer() -> bytearray:
    return make_main_game_buffer()


@pytest.fixture()
def main_game_save_file(tmp_path: Path, main_game_buffer: bytearray) -> Path:
    """Write a synthetic main-game save to a temp file and return its path."""
    path = tmp_path / "bfsgame01.sav"
    path.write_bytes(main_game_buffer)
    return path


@pytest.fixture()
def fc_save_file(tmp_path: Path) -> Path:
    """
    Write a synthetic Future Connected save to a temp file.

    bfsmeria uses the same binary layout as bfsgame, so we reuse
    make_main_game_buffer() with FC-specific field values.
    """
    buf = make_main_game_buffer(money=50_000, nopon_coins=777)
    path = tmp_path / "bfsmeria00.sav"
    path.write_bytes(buf)
    return path
