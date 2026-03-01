"""About dialog — credits and license information."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from xcde_editor import __fork_repo__, __original_repo__, __version__


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About XCDE Save Editor")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("<h2>XCDE Save Editor</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version_lbl = QLabel(f"<b>Version:</b> {__version__}")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_lbl)

        credits_text = (
            f"<p>Forked from <b>MathieuARS</b>'s save editor "
            f"(<a href='{__fork_repo__}'>{__fork_repo__}</a>).</p>"
            "<p>Save-file format originally reverse-engineered by "
            f"<b>damysteryman</b> (<a href='{__original_repo__}'>{__original_repo__}</a>).</p>"
            "<p>Licensed under the <b>GNU General Public License v3.0</b>.<br>"
            "Source code must remain freely available under the same terms.</p>"
            "<p>Modifying save files carries inherent risk. Always keep backups.</p>"
        )
        credits = QLabel(credits_text)
        credits.setWordWrap(True)
        credits.setOpenExternalLinks(True)
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
