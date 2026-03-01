"""Python → binary: patch a SaveData back into its raw buffer and flush to disk."""

from __future__ import annotations

import struct
from pathlib import Path

from xcde_editor.core.constants import (
    AP_OFFSET_IN_MEMBER,
    ARTS_LEVEL_SIZE,
    ARTS_LEVELS_OFFSET,
    EXP_OFFSET_IN_MEMBER,
    LEVEL_OFFSET_IN_MEMBER,
    MAX_AP,
    MAX_ART_LEVEL,
    MAX_ART_UNLOCK,
    MAX_EXP,
    MAX_LEVEL,
    MAX_MONEY,
    MAX_NOPON_COINS,
    MONEY_OFFSET,
    NOPON_COINS_OFFSET,
    PARTY_MEMBER_SIZE,
    PARTY_MEMBERS_OFFSET,
    UNKNOWN_OFFSET_IN_MEMBER,
)
from xcde_editor.core.types import ArtEntry, PartyMember, SaveData
from xcde_editor.core.validator import validate_buffer
from xcde_editor.logging_config import get_logger

log = get_logger("core.writer")


class WriteError(Exception):
    """Raised when a write operation fails post-validation."""


def commit_save(save: SaveData, output_path: Path | None = None) -> Path:
    """
    Patch all fields from *save* into its raw buffer, validate the result,
    and write to disk.

    Args:
        save: The in-memory SaveData (with edits applied).
        output_path: Override destination. Defaults to save.path.

    Returns:
        The path that was written.

    Raises:
        WriteError: if post-write validation fails (file is NOT written in this case).
    """
    dest = output_path or save.path
    _patch_buffer(save)

    # Validate the patched buffer before touching disk
    try:
        validate_buffer(save.raw, save.kind)
    except Exception as exc:
        raise WriteError(
            f"Post-patch validation failed — aborting write to protect your save.\nDetails: {exc}"
        ) from exc

    dest.write_bytes(save.raw)
    log.info("Save written to %s (%d bytes)", dest, len(save.raw))
    return dest


# ---------------------------------------------------------------------------
# Field setters (validate + mutate save in place)
# ---------------------------------------------------------------------------


def set_money(save: SaveData, value: int) -> None:
    _check_range("Money", value, 0, MAX_MONEY)
    save.money = value


def set_nopon_coins(save: SaveData, value: int) -> None:
    _check_range("Nopon coins", value, 0, MAX_NOPON_COINS)
    save.nopon_coins = value


def set_member_level(member: PartyMember, value: int) -> None:
    _check_range("Level", value, 1, MAX_LEVEL)
    member.level = value


def set_member_exp(member: PartyMember, value: int) -> None:
    _check_range("EXP", value, 0, MAX_EXP)
    member.exp = value


def set_member_ap(member: PartyMember, value: int) -> None:
    _check_range("AP", value, 0, MAX_AP)
    member.ap = value


def set_art_level(art: ArtEntry, value: int) -> None:
    _check_range("Art level", value, 0, MAX_ART_LEVEL)
    art.level = value


def set_art_max_unlock(art: ArtEntry, value: int) -> None:
    _check_range("Art max unlock", value, 0, MAX_ART_UNLOCK)
    art.max_unlock = value


# ---------------------------------------------------------------------------
# Internal: patch raw buffer from typed fields
# ---------------------------------------------------------------------------


def _patch_buffer(save: SaveData) -> None:
    _write_u32(save.raw, MONEY_OFFSET, save.money)
    _write_u32(save.raw, NOPON_COINS_OFFSET, save.nopon_coins)

    # bfsgame and bfsmeria share the same layout — patch everything for both.
    for member in save.party:
        _patch_member(save.raw, member)
    for art in save.arts:
        _patch_art(save.raw, art)


def _patch_member(raw: bytearray, member: PartyMember) -> None:
    from xcde_editor.core.parser import character_position  # avoid circular import

    pos = character_position(member.character_id)
    base = PARTY_MEMBERS_OFFSET + pos * PARTY_MEMBER_SIZE

    _write_u32(raw, base + LEVEL_OFFSET_IN_MEMBER, member.level)
    _write_u32(raw, base + EXP_OFFSET_IN_MEMBER, member.exp)
    _write_u32(raw, base + AP_OFFSET_IN_MEMBER, member.ap)

    # Restore the unknown region verbatim
    unk_start = base + UNKNOWN_OFFSET_IN_MEMBER
    raw[unk_start : unk_start + len(member.raw_unknown)] = member.raw_unknown


def _patch_art(raw: bytearray, art: ArtEntry) -> None:
    offset = ARTS_LEVELS_OFFSET + art.index * ARTS_LEVEL_SIZE
    raw[offset] = art.level
    raw[offset + 1] = art.max_unlock


def _write_u32(buf: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", buf, offset, value)


def _check_range(name: str, value: int, lo: int, hi: int) -> None:
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be {lo}-{hi:,}, got {value:,}.")
