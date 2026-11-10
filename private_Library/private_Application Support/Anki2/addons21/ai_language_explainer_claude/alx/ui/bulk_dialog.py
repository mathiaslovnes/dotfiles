"""Confirmation before generating explanations (reviewer: g / Shift+G; Browser: batch).

Always generates both the explanation text and its audio (unless one of them is switched
off in the settings), so there is nothing to choose: Space or Return generates, Esc cancels."""

from __future__ import annotations

from typing import Iterable, Optional

from aqt import mw
from aqt.qt import QDialog, QHBoxLayout, QLabel, QPushButton, Qt, QVBoxLayout
from aqt.utils import qconnect

from ..config import CONFIG
from ..profiles import fcfg, profile_for
from ..logging import debug_log


class BulkGenerationDialog(QDialog):
    def __init__(self, parent=None, selected_notes: Optional[Iterable[int]] = None):
        super().__init__(parent)
        self.setWindowTitle("AI Language Explainer")
        self.setMinimumWidth(420)
        self.selected_notes = list(selected_notes or [])
        self.text_on = not CONFIG.get("disable_text_generation", False)
        self.audio_on = not CONFIG.get("disable_audio", False)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        stats = self._analyze_selected_notes()
        what = {(True, True): "the explanation and its audio", (True, False): "the explanation",
                (False, True): "the explanation audio"}.get((self.text_on, self.audio_on))
        total, matching, existing = len(self.selected_notes), stats["matching_notes"], stats["existing_text"]

        if not what:
            message = "Text and audio generation are both switched off in the settings."
        elif total == 1:
            message = f"Generate {what}?"
            if existing:
                message += "<br>The current one is replaced."
        else:
            message = f"Generate {what} for {matching} notes?"
            if existing:
                message += f"<br>{existing} already {'has' if existing == 1 else 'have'} one, which gets replaced."
            if total > matching:
                message += f"<br>{total - matching} aren't a configured note type and are skipped."
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel, self.generate = QPushButton("Cancel"), QPushButton("Generate")
        self.generate.setDefault(True)
        self.generate.setEnabled(bool(what))
        qconnect(cancel.clicked, self.reject)
        qconnect(self.generate.clicked, self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(self.generate)
        layout.addLayout(buttons)
        self.generate.setFocus()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space and self.generate.isEnabled():
            self.accept()
            return
        super().keyPressEvent(event)

    def _analyze_selected_notes(self) -> dict[str, int]:
        stats = {"matching_notes": 0, "empty_text": 0, "existing_text": 0, "empty_audio": 0, "existing_audio": 0}
        for note_id in self.selected_notes:
            try:
                note = mw.col.get_note(note_id)
                if profile_for(note.note_type()["name"]) is None:
                    continue
                stats["matching_notes"] += 1
                for key, field in (("text", fcfg(note, "explanation_field")),
                                   ("audio", fcfg(note, "explanation_audio_field"))):
                    if field in note:
                        stats[("existing_" if note[field].strip() else "empty_") + key] += 1
            except Exception as err:
                debug_log(f"Error analyzing note {note_id}: {err}")
        return stats

    def get_generation_options(self) -> tuple[bool, bool, bool, bool]:
        """(generate text, generate audio, override text, override audio)"""
        return self.text_on, self.audio_on, self.text_on, self.audio_on


__all__ = ["BulkGenerationDialog"]
