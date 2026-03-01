"""
Typed data structures representing the XCDE save file in memory.

All unknown regions of the binary are preserved verbatim so that
round-tripping the file never corrupts data we don't understand yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class SaveKind(Enum):
    """Type of save file detected from its filename."""

    MAIN_GAME = auto()
    FUTURE_CONNECTED = auto()


@dataclass
class PartyMember:
    """Stats for a single party member, parsed from the save."""

    character_id: int
    level: int
    exp: int
    ap: int
    # The remaining 300 bytes of the 0x138-byte struct are not yet mapped.
    # They are preserved verbatim to avoid corrupting unknown data.
    raw_unknown: bytes = field(repr=False)


@dataclass
class ArtEntry:
    """A single art's level and max unlock tier."""

    index: int
    level: int  # 0-12
    max_unlock: int  # 0-3  (ArtsLevelUnlocked)


@dataclass
class SaveData:
    """Full parsed representation of a XCDE save file."""

    path: Path
    kind: SaveKind
    is_autosave: bool
    money: int
    nopon_coins: int  # present in both save types at 0x000010
    party: list[PartyMember]
    arts: list[ArtEntry]
    # The full raw buffer. Writer patches into this and flushes to disk.
    raw: bytearray = field(repr=False)
