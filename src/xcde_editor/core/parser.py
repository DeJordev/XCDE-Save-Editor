"""Binary → Python: parse a raw save buffer into typed SaveData."""

from __future__ import annotations

import struct
from pathlib import Path

from xcde_editor.core.constants import (
    AP_OFFSET_IN_MEMBER,
    ARTS_LEVEL_SIZE,
    ARTS_LEVELS_OFFSET,
    EXP_OFFSET_IN_MEMBER,
    LEVEL_OFFSET_IN_MEMBER,
    MONEY_OFFSET,
    NOPON_COINS_OFFSET,
    PARTY_MEMBER_SIZE,
    PARTY_MEMBERS_OFFSET,
    PLAYABLE_CHARACTER_IDS,
    TOTAL_ARTS,
    UNKNOWN_OFFSET_IN_MEMBER,
)
from xcde_editor.core.types import ArtEntry, PartyMember, SaveData
from xcde_editor.core.validator import detect_save_kind, validate_buffer
from xcde_editor.logging_config import get_logger

log = get_logger("core.parser")


def load_save(path: Path) -> SaveData:
    """
    Read a save file from disk and return a fully parsed SaveData.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValidationError: if the file fails structural checks.
    """
    if not path.exists():
        raise FileNotFoundError(f"Save file not found: {path}")

    raw = bytearray(path.read_bytes())
    kind, is_autosave = detect_save_kind(path)
    validate_buffer(raw, kind)

    log.info("Loaded %s save: %s (%s bytes)", kind.name, path.name, len(raw))

    # bfsgame and bfsmeria share the same binary layout and offsets.
    money = _read_u32(raw, MONEY_OFFSET)
    nopon_coins = _read_u32(raw, NOPON_COINS_OFFSET)
    party = _parse_party(raw)
    arts = _parse_arts(raw)

    return SaveData(
        path=path,
        kind=kind,
        is_autosave=is_autosave,
        money=money,
        nopon_coins=nopon_coins,
        party=party,
        arts=arts,
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_u32(buf: bytearray, offset: int) -> int:
    return struct.unpack_from("<I", buf, offset)[0]


def _member_base(position: int) -> int:
    return PARTY_MEMBERS_OFFSET + position * PARTY_MEMBER_SIZE


def _parse_party(raw: bytearray) -> list[PartyMember]:
    members: list[PartyMember] = []
    for cid in PLAYABLE_CHARACTER_IDS:
        pos = character_position(cid)
        base = _member_base(pos)
        level = _read_u32(raw, base + LEVEL_OFFSET_IN_MEMBER)
        exp = _read_u32(raw, base + EXP_OFFSET_IN_MEMBER)
        ap = _read_u32(raw, base + AP_OFFSET_IN_MEMBER)
        unknown_start = base + UNKNOWN_OFFSET_IN_MEMBER
        unknown_end = base + PARTY_MEMBER_SIZE
        raw_unknown = bytes(raw[unknown_start:unknown_end])
        members.append(
            PartyMember(
                character_id=cid,
                level=level,
                exp=exp,
                ap=ap,
                raw_unknown=raw_unknown,
            )
        )
    return members


def _parse_arts(raw: bytearray) -> list[ArtEntry]:
    arts: list[ArtEntry] = []
    for i in range(TOTAL_ARTS):
        offset = ARTS_LEVELS_OFFSET + i * ARTS_LEVEL_SIZE
        arts.append(
            ArtEntry(
                index=i,
                level=raw[offset],
                max_unlock=raw[offset + 1],
            )
        )
    return arts


def character_position(character_id: int) -> int:
    """Map a character ID to its index in the PartyMember array."""
    from xcde_editor.core.constants import CHARACTER_POSITIONS, Character

    try:
        char_enum = Character(character_id)
    except ValueError:
        raise ValueError(f"Unknown character ID: {character_id}") from None

    explicit = CHARACTER_POSITIONS.get(char_enum)
    if explicit is not None:
        return explicit

    # For IDs 9-15 not in the explicit map, use sequential positions
    if character_id in PLAYABLE_CHARACTER_IDS:
        return character_id - 1

    raise ValueError(f"Character {char_enum.name} (ID {character_id}) has no known array position.")
