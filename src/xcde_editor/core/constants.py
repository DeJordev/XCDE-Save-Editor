"""
Save file offsets, limits, and enums for Xenoblade Chronicles: Definitive Edition.

Forked from MathieuARS/XCDE-Save-Editor (https://github.com/MathieuARS/XCDE-Save-Editor).
Save-file format originally reverse-engineered by damysteryman (https://gitlab.com/damysteryman/XCDESave).
"""

from __future__ import annotations

from enum import IntEnum

# ---------------------------------------------------------------------------
# Save file identification
# ---------------------------------------------------------------------------

MAIN_GAME_PREFIX = "bfsgame"
FC_PREFIX = "bfsmeria"
AUTOSAVE_SUFFIX = "a.sav"


# ---------------------------------------------------------------------------
# PartyMember array  (bfsgame only)
# ---------------------------------------------------------------------------

PARTY_MEMBERS_OFFSET: int = 0x152368
PARTY_MEMBER_SIZE: int = 0x138  # 312 bytes per member

LEVEL_OFFSET_IN_MEMBER: int = 0x00  # u32 LE
EXP_OFFSET_IN_MEMBER: int = 0x04  # u32 LE
AP_OFFSET_IN_MEMBER: int = 0x08  # u32 LE
UNKNOWN_OFFSET_IN_MEMBER: int = 0x0C  # 300 bytes, preserved as-is


# ---------------------------------------------------------------------------
# Arts array  (bfsgame only)
# ---------------------------------------------------------------------------

ARTS_LEVELS_OFFSET: int = 0x1536E8
ARTS_LEVEL_SIZE: int = 2  # byte 0 = level, byte 1 = max_unlock
TOTAL_ARTS: int = 188


# ---------------------------------------------------------------------------
# Economy  (bfsgame only)
# ---------------------------------------------------------------------------

MONEY_OFFSET: int = 0x151B40  # u32 LE
NOPON_COINS_OFFSET: int = 0x000010  # u32 LE  (main game, confirmed)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

MIN_SAVE_SIZE: int = 0x153860


# ---------------------------------------------------------------------------
# Game limits
# ---------------------------------------------------------------------------

MAX_LEVEL: int = 99
MAX_EXP: int = 9_999_999
MAX_AP: int = 9_999_999
MAX_ART_LEVEL: int = 12
MAX_ART_UNLOCK: int = 3
MAX_MONEY: int = 99_999_999
MAX_NOPON_COINS: int = 999_999


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Character(IntEnum):
    """Character IDs for Xenoblade Chronicles: Definitive Edition."""

    NONE = 0
    SHULK = 1
    REYN = 2
    FIORA = 3
    DUNBAN = 4
    SHARLA = 5
    RIKI = 6
    MELIA = 7
    FIORA_2 = 8
    DICKSON = 9
    MUMKHAR = 10
    ALVIS = 11
    DUNBAN_2 = 12
    DUNBAN_3 = 13
    KINO = 14
    NENE = 15
    # Non-playable / Future Connected party
    WUNWUN = 16
    TUTU = 17
    DRYDRY = 18
    FOFORA = 19
    FAIFA = 20
    HEKASA = 21
    SETSET = 22
    TEITEI = 23
    NONONA = 24
    DEKADEKA = 25
    EVELEN = 26
    TENTOO = 27


class ArtsLevelUnlocked(IntEnum):
    """Maximum level tier that an art can be upgraded to."""

    IV_BEGINNER = 0  # up to level 4
    VII_INTERMEDIATE = 1  # up to level 7
    X_EXPERT = 2  # up to level 10
    XII_MASTER = 3  # up to level 12


# ---------------------------------------------------------------------------
# Character → array position mapping
# ---------------------------------------------------------------------------

# Explicitly verified positions in the PartyMember array
CHARACTER_POSITIONS: dict[Character, int] = {
    Character.SHULK: 0,
    Character.REYN: 1,
    Character.FIORA: 2,
    Character.DUNBAN: 3,
    Character.SHARLA: 4,
    Character.RIKI: 5,
    Character.MELIA: 6,
    Character.FIORA_2: 7,
}

# IDs considered safely editable (all playable characters)
PLAYABLE_CHARACTER_IDS: list[int] = list(range(1, 16))


# ---------------------------------------------------------------------------
# Character display groups
# Each entry: (section_label, [character_ids])
# ---------------------------------------------------------------------------

# Main game (bfsgame): three visual sections
CHAR_GROUPS_MAIN: list[tuple[str, list[int]]] = [
    ("Main Party", [1, 2, 3, 4, 5, 6, 7, 8]),  # Shulk … Fiora_2 — full XP/AP
    ("Guest / Temporary", [9, 10, 11, 12, 13]),  # Dickson … Dunban_3 — level only
    ("Future Connected", [14, 15]),  # Kino, Nene — level only in main game
]

# Future Connected (bfsmeria): two visual sections
CHAR_GROUPS_FC: list[tuple[str, list[int]]] = [
    ("FC Party", [7, 14, 15]),  # Melia, Kino, Nene — full XP/AP
    ("Guest / Crossover", [1]),  # Shulk joins Melia in FC
    ("Main Game Characters", [2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]),  # inherited, no XP/AP
]
