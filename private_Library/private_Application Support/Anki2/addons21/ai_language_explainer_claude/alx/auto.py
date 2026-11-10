"""Generate the explanation (and its audio) automatically for newly added notes.

A new note is watched until both the word and the sentence field are filled, so
mining with Yomitan first (word + definition) and mpv afterwards (sentence +
picture) works: generation starts once mpv has added the sentence. Book cards,
which have the sentence from the start, are done right away. A note whose
sentence doesn't arrive within WAIT_MINUTES is left alone (press g on it).

Only note types the add-on is set up for, only into empty fields; the note is
re-read right before saving, so nothing another tool wrote is overwritten.
Turn off with "auto_generate_on_add": false in the add-on config."""

from __future__ import annotations

import os
import threading
import time
import traceback

from aqt import mw
from aqt.utils import tooltip

from .config import CONFIG
from .logging import debug_log
from .profiles import fcfg, profile_for
from ..api_handler import generate_audio as backend_generate_audio, generate_explanation

WAIT_MINUTES = 15
_pending = []   # notes just added; their id is set once add_note returns
_watch = {}     # note id -> deadline
_timer = None


def on_note_will_be_added(col, note, deck_id) -> None:
    try:
        if not CONFIG.get("auto_generate_on_add", True) or CONFIG.get("disable_text_generation"):
            return
        if not CONFIG.get("api_key") or profile_for(note.note_type()["name"]) is None:
            return
        _pending.append(note)
        mw.progress.single_shot(300, _collect_ids, False)
    except Exception:
        debug_log("auto: " + traceback.format_exc())


def _collect_ids() -> None:
    global _timer
    while _pending:
        note = _pending.pop(0)
        if note.id:
            _watch[note.id] = time.time() + WAIT_MINUTES * 60
    _check()
    if _watch and _timer is None:
        _timer = mw.progress.timer(3000, _check, True, parent=mw)


def _check() -> None:
    global _timer
    now = time.time()
    for nid, deadline in list(_watch.items()):
        try:
            note = mw.col.get_note(nid)
        except Exception:
            _watch.pop(nid, None)          # deleted
            continue
        wf, sf, ef = fcfg(note, "word_field"), fcfg(note, "sentence_field"), fcfg(note, "explanation_field")
        word = note[wf] if wf in note else ""
        sentence = note[sf] if sf in note else ""
        if ef in note and note[ef].strip():
            _watch.pop(nid, None)          # already has one (e.g. g was pressed)
        elif word.strip() and sentence.strip():
            _watch.pop(nid, None)
            threading.Thread(target=_generate, args=(nid, word, sentence), daemon=True).start()
        elif now > deadline:
            _watch.pop(nid, None)
            debug_log(f"auto: note {nid} got no sentence within {WAIT_MINUTES} min, skipped")
    if not _watch and _timer is not None:
        _timer.stop()
        _timer = None


def _generate(nid, word, sentence) -> None:
    try:
        prompt = CONFIG["prompt"].format(word=word, sentence=sentence, definition="")
        text = generate_explanation(CONFIG["api_key"], prompt, CONFIG["model"])
        sound = None
        if not CONFIG.get("disable_audio"):
            try:  # audio failing (e.g. AivisSpeech not running) must not cost the text
                engine = CONFIG.get("tts_engine")
                style = (CONFIG.get("aivisspeech_style_id") if engine == "AivisSpeech"
                         else CONFIG.get("voicevox_style_id") if engine == "VoiceVox" else None)
                path = backend_generate_audio(CONFIG.get("api_key", ""), text, style_id_override=style)
                if path:
                    path = str(path)
                    sound = path if path.startswith("[sound:") else f"[sound:{os.path.basename(path)}]"
            except Exception as e:
                debug_log(f"auto: audio failed for note {nid}: {e}")
        mw.taskman.run_on_main(lambda: _save(nid, text, sound, word))
    except Exception as e:
        debug_log(f"auto: generation failed for note {nid}: {e}")
        mw.taskman.run_on_main(lambda: tooltip(f"解説 failed for {word[:20]}: {str(e)[:80]}"))


def _save(nid, text, sound, word) -> None:
    try:
        note = mw.col.get_note(nid)   # fresh copy: keeps whatever was added meanwhile
    except Exception:
        return                        # note was deleted
    changed = False
    ef, af = fcfg(note, "explanation_field"), fcfg(note, "explanation_audio_field")
    if text and ef in note and not note[ef].strip():
        note[ef] = text
        changed = True
    if sound and af in note and not note[af].strip():
        note[af] = sound
        changed = True
    if changed:
        mw.col.update_note(note)
        tooltip(f"解説 added: {word[:20]}")
        if mw.state == "review" and mw.reviewer.card and mw.reviewer.card.nid == nid:
            mw.reviewer._redraw_current_card()


__all__ = ["on_note_will_be_added"]
