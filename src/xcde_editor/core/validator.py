"""Save file validation — run before reading and after writing."""

from __future__ import annotations

import struct
from pathlib import Path

from xcde_editor.core.constants import (
    AP_OFFSET_IN_MEMBER,
    ARTS_LEVEL_SIZE,
    ARTS_LEVELS_OFFSET,
    CHARACTER_POSITIONS,
    FC_PREFIX,
    MAIN_GAME_PREFIX,
    MIN_SAVE_SIZE,
    PARTY_MEMBER_SIZE,
    PARTY_MEMBERS_OFFSET,
    TOTAL_ARTS,
)
from xcde_editor.core.types import SaveKind


class ValidationError(Exception):
    """Raised when a save file fails integrity checks."""


def detect_save_kind(path: Path) -> tuple[SaveKind, bool]:
    """
    Determine save type and whether it is an autosave from the filename.

    Returns:
        (SaveKind, is_autosave)

    Raises:
        ValidationError: if the filename does not match any known pattern.
    """
    name = path.name.lower()
    is_autosave = name.endswith("a.sav")

    if name.startswith(MAIN_GAME_PREFIX):
        return SaveKind.MAIN_GAME, is_autosave
    if name.startswith(FC_PREFIX):
        return SaveKind.FUTURE_CONNECTED, is_autosave

    raise ValidationError(
        f"Unrecognized save filename: '{path.name}'. "
        f"Expected 'bfsgame*.sav' (main game) or 'bfsmeria*.sav' (Future Connected)."
    )


def validate_buffer(data: bytes | bytearray, kind: SaveKind) -> None:
    """
    Run structural integrity checks on a raw save buffer.

    Both bfsgame and bfsmeria use the same binary layout, so the same
    validation rules apply regardless of save kind.

    Raises:
        ValidationError: with a human-readable description of the problem.
    """
    _validate_save(data, kind)


def _validate_save(data: bytes | bytearray, kind: SaveKind) -> None:
    size = len(data)
    kind_label = "main-game" if kind is SaveKind.MAIN_GAME else "Future Connected"

    if size < MIN_SAVE_SIZE:
        raise ValidationError(
            f"File too small ({size:,} bytes). "
            f"A {kind_label} save must be at least {MIN_SAVE_SIZE:,} bytes."
        )

    # Check the furthest byte we will ever read/write is in bounds
    max_party_end = (
        PARTY_MEMBERS_OFFSET
        + (max(CHARACTER_POSITIONS.values()) * PARTY_MEMBER_SIZE)
        + AP_OFFSET_IN_MEMBER
        + 4
    )
    max_arts_end = ARTS_LEVELS_OFFSET + (TOTAL_ARTS * ARTS_LEVEL_SIZE)
    required = max(max_party_end, max_arts_end)

    if size < required:
        raise ValidationError(
            f"File too small ({size:,} bytes) to contain all expected data "
            f"(need at least {required:,} bytes). Is this really a XCDE save?"
        )

    # Sanity-check: first u32 of the first party member should be a plausible level
    first_level = struct.unpack_from("<I", data, PARTY_MEMBERS_OFFSET)[0]
    if first_level > 99:
        raise ValidationError(
            f"Unexpected value at PartyMember[0].level offset "
            f"(0x{PARTY_MEMBERS_OFFSET:X}): {first_level}. "
            "File may be corrupted or this is not a XCDE save."
        )
