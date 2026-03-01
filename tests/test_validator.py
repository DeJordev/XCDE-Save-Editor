"""Tests for core/validator.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from xcde_editor.core.types import SaveKind
from xcde_editor.core.validator import ValidationError, detect_save_kind, validate_buffer

# ---------------------------------------------------------------------------
# detect_save_kind
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename,expected_kind,expected_auto",
    [
        ("bfsgame01.sav", SaveKind.MAIN_GAME, False),
        ("bfsgame01a.sav", SaveKind.MAIN_GAME, True),
        ("bfsgame00.sav", SaveKind.MAIN_GAME, False),
        ("bfsgame00a.sav", SaveKind.MAIN_GAME, True),
        ("bfsmeria00.sav", SaveKind.FUTURE_CONNECTED, False),
        ("bfsmeria00a.sav", SaveKind.FUTURE_CONNECTED, True),
        ("bfsmeria01.sav", SaveKind.FUTURE_CONNECTED, False),
    ],
)
def test_detect_save_kind(filename: str, expected_kind: SaveKind, expected_auto: bool) -> None:
    kind, is_auto = detect_save_kind(Path(filename))
    assert kind is expected_kind
    assert is_auto is expected_auto


def test_detect_save_kind_unknown_raises() -> None:
    with pytest.raises(ValidationError, match="Unrecognized save filename"):
        detect_save_kind(Path("unknownfile.sav"))


def test_detect_save_kind_autosave_not_confused_with_fc() -> None:
    """bfsgame00a.sav must be MAIN_GAME autosave, not Future Connected."""
    kind, is_auto = detect_save_kind(Path("bfsgame00a.sav"))
    assert kind is SaveKind.MAIN_GAME
    assert is_auto is True


# ---------------------------------------------------------------------------
# validate_buffer — main game
# ---------------------------------------------------------------------------


def test_validate_main_game_ok(main_game_buffer: bytearray) -> None:
    validate_buffer(main_game_buffer, SaveKind.MAIN_GAME)  # should not raise


def test_validate_main_game_too_small() -> None:
    with pytest.raises(ValidationError, match="too small"):
        validate_buffer(bytearray(100), SaveKind.MAIN_GAME)


def test_validate_main_game_implausible_level(main_game_buffer: bytearray) -> None:
    import struct

    from xcde_editor.core.constants import PARTY_MEMBERS_OFFSET

    struct.pack_into("<I", main_game_buffer, PARTY_MEMBERS_OFFSET, 9999)
    with pytest.raises(ValidationError, match="Unexpected value"):
        validate_buffer(main_game_buffer, SaveKind.MAIN_GAME)


# ---------------------------------------------------------------------------
# validate_buffer — future connected
# ---------------------------------------------------------------------------


def test_validate_fc_ok(main_game_buffer: bytearray) -> None:
    # FC saves share the same layout and minimum size as main-game saves.
    validate_buffer(main_game_buffer, SaveKind.FUTURE_CONNECTED)


def test_validate_fc_too_small() -> None:
    with pytest.raises(ValidationError, match="too small"):
        validate_buffer(bytearray(4), SaveKind.FUTURE_CONNECTED)
