"""Leech Scaffold: show the sentence on the front of struggling leeches, and take it
away again once they hold.

  on:  tagged `leech`, failed in the last <failed_within_days> days, interval below
       <graduate_interval_days>, not suspended, sentence-card field empty
       -> field = "scaffold", tag `leech-scaffold`
  off: tagged `leech-scaffold` and interval >= <graduate_interval_days>
       -> field cleared (only if it still says "scaffold"), tag removed

Your own sentence cards (any other value in the field) are never touched.
Runs after every sync and from Tools > Leech scaffold: update now.
Settings: Tools > Add-ons > Leech Scaffold > Config."""

from __future__ import annotations

import traceback

from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import qconnect, tooltip

VALUE = "scaffold"
TAG = "leech-scaffold"
DEFAULTS = {
    "enabled": True,
    "fields": {"subs2srs": "sentence-card", "core6k": "Sentence-Card"},
    "graduate_interval_days": 30,
    "failed_within_days": 90,
}


def _config() -> dict:
    cfg = dict(DEFAULTS)
    cfg.update(mw.addonManager.getConfig(__name__) or {})
    return cfg


def run_scaffold(quiet: bool = True) -> None:
    cfg = _config()
    if mw.col is None or not cfg["enabled"]:
        return
    try:
        col = mw.col
        ivl, days = int(cfg["graduate_interval_days"]), int(cfg["failed_within_days"])
        changed, on, off = [], 0, 0
        for nt, field in cfg["fields"].items():
            for nid in col.find_notes(f'"note:{nt}" tag:{TAG} prop:ivl>={ivl}'):
                note = col.get_note(nid)
                if field in note and note[field].strip() == VALUE:
                    note[field] = ""
                note.remove_tag(TAG)
                changed.append(note)
                off += 1
            query = f'"note:{nt}" tag:leech rated:{days}:1 prop:ivl<{ivl} -is:suspended -tag:{TAG}'
            for nid in col.find_notes(query):
                note = col.get_note(nid)
                if field not in note or note[field].strip():
                    continue                    # your own sentence card: leave it
                note[field] = VALUE
                note.add_tag(TAG)
                changed.append(note)
                on += 1
        if changed:
            col.update_notes(changed)
        if changed or not quiet:
            tooltip(f"Leech scaffold: {on} → sentence front, {off} → back to word-only")
    except Exception:
        print("leech_scaffold:", traceback.format_exc())
        if not quiet:
            tooltip("Leech scaffold failed (see Tools > Add-ons > Leech Scaffold).")


def _after_sync() -> None:
    mw.progress.single_shot(1000, run_scaffold)


gui_hooks.sync_did_finish.append(_after_sync)
_action = QAction("Leech scaffold: update now", mw)
qconnect(_action.triggered, lambda: run_scaffold(quiet=False))
mw.form.menuTools.addAction(_action)
