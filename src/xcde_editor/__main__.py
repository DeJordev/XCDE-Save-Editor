"""Entry point for the XCDE Save Editor application."""

from __future__ import annotations

import sys

from xcde_editor.logging_config import setup_logging


def main() -> None:
    setup_logging()

    # Import Qt here so logging is configured first
    from PyQt6.QtWidgets import QApplication

    from xcde_editor.ui.app import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("XCDE Save Editor")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("xcde-editor")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
