"""Word Audio Picker: choose the word audio for a card from the Local Audio Server.

The 音 button in the editor (Browser, Edit and Add windows) lists the recordings the
Local Audio Server has for the card's word: NHK16, SMK8, Forvo, JPod. ▶ plays one, Use puts
it in the word audio field. The recording in the field now is marked. Fields and the
server address are in this add-on's config."""

from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.parse
import urllib.request

from aqt import gui_hooks, mw
from aqt.qt import (QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea, Qt,
                    QVBoxLayout, QWidget)
from aqt.sound import av_player
from aqt.utils import qconnect, tooltip

ADDON = __name__.split(".")[0]


def cfg() -> dict:
    return mw.addonManager.getConfig(ADDON) or {}


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>|&nbsp;", "", s or "")
    s = re.sub(r"\[[^\]]*\]", "", s)              # furigana brackets 漢字[かんじ]
    return re.sub(r"\s+", "", s)


def hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def word_and_reading(note) -> tuple[str, str]:
    c = cfg()
    wf = c.get("word_field", "word")
    word = clean(note[wf]) if wf in note else ""
    reading = ""
    for rf in c.get("reading_fields", ["reading-plain", "reading"]):
        if rf in note:
            r = re.sub(r"[^ぁ-ゖァ-ヺー]", "", hira(clean(note[rf])))
            if r:
                reading = r
                break
    return word, reading


def media_name(url: str) -> str:
    """http://localhost:5050/nhk16/audio/2017….mp3 -> local_nhk16_2017….mp3 (the names the
    cards already use); Forvo keeps the speaker, since each speaker's file has the word's name."""
    parts = [urllib.parse.unquote(p) for p in urllib.parse.urlparse(url).path.split("/") if p]
    if not parts:
        return "local_audio.mp3"
    source = parts[0]
    if source == "forvo" and len(parts) >= 3:
        return f"local_forvo_{parts[1]}_{parts[-1]}"
    return f"local_{source}_{parts[-1]}"


def fetch_list(word: str, reading: str) -> list:
    url = cfg().get("server_url", "http://127.0.0.1:5050/?term={term}&reading={reading}")
    url = url.replace("{term}", urllib.parse.quote(word)).replace("{reading}", urllib.parse.quote(reading))
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [(s.get("name", "?"), s["url"]) for s in data.get("audioSources", []) if s.get("url")]


def download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=15) as r:
        return r.read()


class PickerDialog(QDialog):
    def __init__(self, editor, word, reading, sources, current):
        super().__init__(editor.parentWindow)
        self.editor, self.sources = editor, sources
        font = self.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        self.setFont(font)
        self.setWindowTitle(f"Word audio: {word}（{reading}）" if reading else f"Word audio: {word}")
        outer = QVBoxLayout(self)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        for i, (name, url) in enumerate(sources):
            row = QHBoxLayout()
            play = QPushButton("▶")
            play.setFixedWidth(44)
            play.setAutoDefault(False)
            qconnect(play.clicked, lambda _=False, u=url: self.play(u))
            label = QLabel(f"<b>{name}</b>  ✓ in the card now" if media_name(url) == current else name)
            use = QPushButton("Use")
            use.setAutoDefault(False)
            qconnect(use.clicked, lambda _=False, u=url: self.use(u))
            row.addWidget(play)
            row.addWidget(label, 1)
            row.addWidget(use)
            lay.addLayout(row)
        lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        close = QPushButton("Close")
        qconnect(close.clicked, self.reject)
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close)
        outer.addLayout(bottom)
        self.resize(520, min(120 + 52 * len(sources), 600))

    def play(self, url: str) -> None:
        def done(fut):
            try:
                data = fut.result()
            except Exception as e:
                tooltip(f"Couldn't load it: {e}", parent=self)
                return
            path = os.path.join(tempfile.gettempdir(), "word_audio_picker_" + media_name(url))
            with open(path, "wb") as f:
                f.write(data)
            av_player.play_file(path)
        mw.taskman.run_in_background(lambda: download(url), done)

    def use(self, url: str) -> None:
        editor = self.editor

        def done(fut):
            try:
                data = fut.result()
            except Exception as e:
                tooltip(f"Couldn't load it: {e}", parent=self)
                return
            name = mw.col.media.write_data(media_name(url), data)   # renamed if the name is taken by other data
            field = cfg().get("audio_field", "word-audio")
            note = editor.note
            if note is None or field not in note:
                tooltip(f"This note has no {field} field.", parent=self)
                return
            note[field] = f"[sound:{name}]"
            if editor.addMode:
                editor.loadNote()
            else:
                from aqt.operations.note import update_note
                update_note(parent=editor.widget, note=note).success(
                    lambda _: editor.loadNoteKeepingFocus()).run_in_background()
            tooltip("Word audio replaced", parent=editor.parentWindow)
            self.accept()

        # save what's typed in the editor first, so nothing is lost when the note reloads
        editor.call_after_note_saved(lambda: mw.taskman.run_in_background(lambda: download(url), done))


def open_picker(editor) -> None:
    note = editor.note
    if note is None:
        return
    word, reading = word_and_reading(note)
    if not word:
        tooltip("No word on this note.", parent=editor.parentWindow)
        return
    field = cfg().get("audio_field", "word-audio")
    m = re.search(r"\[sound:([^\]]+)\]", note[field]) if field in note else None
    current = m.group(1) if m else ""

    def done(fut):
        try:
            sources = fut.result()
        except Exception as e:
            tooltip(f"Local Audio Server didn't answer: {e}", parent=editor.parentWindow)
            return
        if not sources:
            tooltip(f"No recordings for {word}", parent=editor.parentWindow)
            return
        PickerDialog(editor, word, reading, sources, current).exec()

    mw.taskman.run_in_background(lambda: fetch_list(word, reading), done)


def add_button(buttons: list, editor) -> None:
    buttons.append(editor.addButton(icon=None, cmd="word_audio_picker", func=open_picker,
                                    tip="Word audio: pick a recording", label="音"))


gui_hooks.editor_did_init_buttons.append(add_button)
