# XCDE Save Editor

A modern GUI save editor for **Xenoblade Chronicles: Definitive Edition** — no Python or command line required.

---

## Credits

This project is a fork of **MathieuARS**'s
[XCDE-Save-Editor](https://github.com/MathieuARS/XCDE-Save-Editor),
reimplemented as a full Python/PyQt6 GUI application.

The save-file format was originally reverse-engineered by **damysteryman** in the
[XCDESave](https://gitlab.com/damysteryman/XCDESave) C# library, which both
projects are built upon.

---

## Features

- Load any main-game (`bfsgame*.sav`) or Future Connected (`bfsmeria*.sav`) save
- Automatically detects autosaves (suffix `a`) and labels them clearly
- **Characters tab** — edit Level, EXP and AP per character; bulk-set all levels at once
- **Arts tab** — edit level and max-unlock tier for all 188 arts; bulk-set all at once
- **Economy tab** — edit Money and Nopon Coins (main game only)
- **Backups tab** — full versioned backup history; restore, export or import with one click
- **Logs tab** — live log viewer with configurable verbosity level
- Remembers the last saves folder between sessions
- Every write is preceded by an automatic backup — you can never lose data

---

## Download

Go to [Releases](../../releases) and download the binary for your platform.
No installation needed — just run the file.

| Platform | File |
|----------|------|
| Windows  | `xcde-save-editor-windows.exe` |
| macOS    | `xcde-save-editor-macos` |
| Linux    | `xcde-save-editor-linux` |

> **macOS / Linux:** you may need to make the file executable:
> `chmod +x xcde-save-editor-macos && ./xcde-save-editor-macos`

---

## Save file locations

| Platform | Path |
|----------|------|
| **Ryujinx** | `%AppData%\Ryujinx\bis\user\save\<title-id>\0\` (Windows) |
| **Yuzu / Suyu / Eden** | `%AppData%\yuzu\nand\user\save\<title-id>\<uid>\` (Windows) |
| **Switch** | Requires custom firmware (e.g. Atmosphere) to access the SD card |

Save file naming:

| File | Contents |
|------|----------|
| `bfsgame00.sav` | Main game, slot 0, manual save |
| `bfsgame00a.sav` | Main game, slot 0, **autosave** |
| `bfsmeria00.sav` | Future Connected, slot 0, manual save |
| `bfsmeria00a.sav` | Future Connected, slot 0, **autosave** |

---

## Safety

- A timestamped backup is **always created automatically** before any write.
- Backups are stored in `.xcde_backups/<savename>/` inside your saves folder.
- All unknown bytes in the save file are preserved verbatim — only fields that are explicitly understood are ever modified.

> **Warning:** Modifying save files carries inherent risk. Keep external copies of saves you care about.

---

## Project structure

```
src/xcde_editor/
├── core/           Binary parsing, writing, and validation
├── backup/         Versioned backup management
└── ui/             PyQt6 GUI (tabs, dialogs)

tests/              Pytest suite (parser, writer, validator, backup)
build/              PyInstaller spec
.github/workflows/  CI (lint + test) and Release (multi-platform build)
```

---

## Running from source

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/DeJordev/XCDE-Save-Editor.git
cd XCDE-Save-Editor
uv sync
uv run python -m xcde_editor
```

Run tests:

```bash
uv run pytest
```

---

## Roadmap

- [ ] Inventory editor (offsets under investigation)
- [ ] Affinity chart editor (offsets under investigation)
- [ ] Future Connected character/arts support
- [ ] `bfssystem.sav` support
- [ ] Dark mode / theme switcher

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

As required by GPLv3, the full source code is available in this repository.
Any distributed binary must be accompanied by access to this source code.
