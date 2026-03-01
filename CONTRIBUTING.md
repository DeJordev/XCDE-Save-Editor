# Contributing to XCDE Save Editor

Thank you for your interest in contributing! This guide explains how the project is structured and how to add new functionality safely.

---

## Development setup

```bash
# Clone the repo
git clone <this-repo>
cd XCDE-Save-Editor

# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies
uv sync

# Run the editor
uv run python -m xcde_editor

# Run tests
uv run pytest

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run pyright src/
```

---

## Code conventions

- Python 3.13+, `from __future__ import annotations` in every file
- All public functions and classes must have type annotations
- Use `dataclasses` or `TypedDict` for data structures — no plain dicts for domain objects
- Logging via `get_logger("module.name")` from `xcde_editor.logging_config`
- No `print()` in library code — use `log.debug/info/warning/error`
- Format: Ruff (100 char line length). Run `uv run ruff format .` before committing.
- Tests must pass: `uv run pytest`
- Type check must pass: `uv run pyright src/`

---

## How to add a new editable field

### 1. Find the offset

Use a hex editor (e.g. HxD, ImHex) to locate the field in the save file:

1. Note the current value in-game
2. Open `bfsgame0x.sav` in a hex editor
3. Search for the value as a little-endian u32 (`struct.pack("<I", value)`)
4. Modify it, save, load in the emulator, confirm it changed

### 2. Add the offset to `core/constants.py`

```python
# Give it a clear name and a comment with the hex address
MY_NEW_FIELD_OFFSET: int = 0xABCDEF  # u32 LE  (0–some_max)
MAX_MY_NEW_FIELD: int = 99_999
```

### 3. Add a field to `core/types.py`

Add the field to `SaveData` (or `PartyMember` if it's per-character):

```python
@dataclass
class SaveData:
    ...
    my_new_field: int  # description
```

### 4. Read it in `core/parser.py`

Inside `load_save()`, alongside the other field reads:

```python
my_new_field = _read_u32(raw, MY_NEW_FIELD_OFFSET)
```

And pass it to `SaveData(...)`.

### 5. Write it in `core/writer.py`

Add a setter with validation:

```python
def set_my_new_field(save: SaveData, value: int) -> None:
    _check_range("My new field", value, 0, MAX_MY_NEW_FIELD)
    save.my_new_field = value
```

And patch it in `_patch_buffer()`:

```python
_write_u32(save.raw, MY_NEW_FIELD_OFFSET, save.my_new_field)
```

### 6. Add a UI control

Add a `QSpinBox` (or equivalent) in the appropriate tab in `src/xcde_editor/ui/widgets/`.
Follow the pattern in `economy_tab.py`.

### 7. Add tests

Add a round-trip test in `tests/test_writer.py`:

```python
def test_round_trip_my_new_field(main_game_save_file: Path) -> None:
    save = load_save(main_game_save_file)
    set_my_new_field(save, 12345)
    commit_save(save)
    reloaded = load_save(main_game_save_file)
    assert reloaded.my_new_field == 12345
```

---

## How to add inventory support

The 300 bytes at `PartyMember.raw_unknown` (offset `+0x0C` within each member's 0x138-byte block) likely contain equipment, gem slots, and other per-character data. The original C# library by damysteryman has partial support for this.

To add inventory support:

1. Cross-reference the upstream Python editor at https://github.com/MathieuARS/XCDE-Save-Editor and the original C# library at https://gitlab.com/damysteryman/XCDESave for known offsets within the member struct
2. Add named fields to `PartyMember` in `core/types.py` for each confirmed offset
3. Remove those bytes from `raw_unknown` and parse them explicitly in `core/parser.py`
4. Add corresponding writers in `core/writer.py`
5. Add an `InventoryTab` widget in `src/xcde_editor/ui/widgets/inventory_tab.py`
6. Register the tab in `ui/app.py`

---

## How to add affinity chart support

The affinity chart (relationships between characters) is stored in an as-yet unmapped region of `bfsgame*.sav`. To contribute:

1. Use the same hex-search methodology described above, targeting known affinity values
2. Document the discovered offsets in `core/constants.py` with a comment
3. Follow the same pattern as any other field

A stub file `core/affinity.py` can be added when offsets are confirmed.

---

## Pull request checklist

- [ ] `uv run ruff check src/ tests/` passes with no errors
- [ ] `uv run ruff format --check src/ tests/` passes
- [ ] `uv run pyright src/` passes in strict mode
- [ ] `uv run pytest` — all tests green, new functionality has tests
- [ ] New offsets are documented in `core/constants.py` with source/method of discovery
- [ ] No `print()` calls in library code
