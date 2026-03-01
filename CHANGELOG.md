# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.0] — 2026-03-01

### Added

- Full GUI application (PyQt6) — no command line required
- **Characters tab**: edit Level, EXP, AP per character; bulk-set all levels
- **Arts tab**: edit level and max-unlock tier for all 188 arts; bulk-set all
- **Economy tab**: edit Money and Nopon Coins (main-game saves only)
- **Backups tab**: versioned backup history with restore, export, import
- **Logs tab**: live log viewer with configurable verbosity level
- Automatic backup before every write (always on, non-negotiable)
- Configurable backup limit per save (default: 20, pruning oldest first)
- Confirmation dialogs for all destructive actions
- Session persistence: remembers last saves folder
- Correct save-type detection by filename prefix (`bfsgame` vs `bfsmeria`)
- Correct autosave detection by filename suffix (`a.sav`)
- `bfssystem.sav` gracefully rejected with a clear error
- PyInstaller packaging for Windows, Linux, macOS (single-file executables)
- GitHub Actions: CI workflow (lint + typecheck + tests) and release workflow (matrix build → GitHub Releases)

### Fixed (vs original CLI script)

- `bfsgame00a.sav` was incorrectly identified as a Future Connected save — now correctly identified as a main-game autosave
- Nopon Coins were incorrectly associated with `bfsmeria` (Future Connected) saves — they belong to `bfsgame` (main game) at offset `0x000010`

### Technical

- Layered architecture: `core/` (parsing), `backup/` (versioning), `ui/` (GUI)
- Strict type annotations throughout (`from __future__ import annotations`, Pyright strict)
- All unknown bytes in the save binary are preserved verbatim
- 38 automated tests covering parser, writer, validator, and backup manager

### Credits

Forked from **MathieuARS**'s
[XCDE-Save-Editor](https://github.com/MathieuARS/XCDE-Save-Editor).
Save-file format originally reverse-engineered by **damysteryman**
([XCDESave](https://gitlab.com/damysteryman/XCDESave), GPLv3).
