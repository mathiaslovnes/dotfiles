"""Name bold: bold a name once in a sentence and every other sentence that has it gets it bolded too.

- Bold a name in the sentence field (Ctrl+B) and leave the field: all other sentences with that
  name get it bolded. Undo with Ctrl+Z.
- Cards added or edited outside the editor (mpv, Yomitan, AnkiMobile) are handled when the
  profile opens and after every sync: names bolded there are learned, and known names are
  bolded in new sentences.
- Only the sentence field of the subs2srs note type is read and changed. Honorifics are left
  outside the bold (<b>槙島</b>君). Names shorter than 2 characters are not spread.
- Tools > Name bold > "Stop bolding a name..." removes a name everywhere and never re-learns it.
"""
import json
import os

from aqt import gui_hooks, mw
from aqt.operations import CollectionOp
from aqt.qt import QAction, QMenu
from aqt.utils import getText, tooltip

from . import core

NOTE_TYPE = "subs2srs"
FIELD = "sentence"
STATE = os.path.join(os.path.dirname(__file__), "user_files", "state.json")


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"ignored": [], "last_mod": 0}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def field_index(col):
    m = col.models.by_name(NOTE_TYPE)
    if not m:
        return None, None
    names = [f["name"] for f in m["flds"]]
    return m["id"], (names.index(FIELD) if FIELD in names else None)


def rows(col, mid, since=0):
    return col.db.all("select id, mod, flds from notes where mid = ? and mod > ?", mid, since)


def known_names(col, mid, idx, ignored):
    out = set()
    for _, _, flds in col.db.all("select id, mod, flds from notes where mid = ? and flds like '%<b>%'", mid):
        out |= core.names_in(flds.split("\x1f")[idx])
    return out - set(ignored)


def apply(col, mid, idx, rx, only=None, skip=None):
    """Bold with rx in every sentence (or only the given note ids). Returns changed notes."""
    changed = []
    q = rows(col, mid) if only is None else [r for r in rows(col, mid) if r[0] in only]
    for nid, _, flds in q:
        if nid == skip:
            continue
        s = flds.split("\x1f")[idx]
        new = core.bold(s, rx)
        if new != s:
            note = col.get_note(nid)
            note[FIELD] = new
            changed.append(note)
    return changed


def run(op_name, fn):
    def do(col):
        pos = col.add_custom_undo_entry(op_name)
        notes = fn(col)
        if notes:
            col.update_notes(notes)
        out = col.merge_undo_entries(pos)
        do.count = len(notes)
        return out
    do.count = 0
    CollectionOp(parent=mw, op=do).success(
        lambda _: tooltip(f"{op_name}: {do.count} sentences") if do.count else None).run_in_background()


# ---------------------------------------------------------------- after sync / on open

def catch_up(*_):
    col = mw.col
    if not col:
        return
    mid, idx = field_index(col)
    if idx is None:
        return
    st = load_state()
    since = st.get("last_mod", 0)
    recent = rows(col, mid, since)
    if not recent and since:
        return
    new_names = set()
    for _, _, flds in recent:
        new_names |= core.names_in(flds.split("\x1f")[idx])
    known = known_names(col, mid, idx, st["ignored"])
    recent_ids = {r[0] for r in recent}
    last = max([since] + [r[1] for r in recent])

    def fn(col):
        out = {}
        # names bolded since last time (phone, AnkiConnect): spread them everywhere
        rx_new = core.compile_names(new_names - set(st["ignored"]))
        for n in apply(col, mid, idx, rx_new) if (rx_new and since) else []:
            out[n.id] = n
        # new or edited sentences: bold every known name in them (first run: everywhere)
        rx_all = core.compile_names(known)
        for n in apply(col, mid, idx, rx_all, only=None if not since else recent_ids):
            if n.id in out:
                out[n.id][FIELD] = core.bold(out[n.id][FIELD], rx_all)
            else:
                out[n.id] = n
        st["last_mod"] = int(__import__("time").time()) if not since else last
        save_state(st)
        return list(out.values())

    run("Bold names", fn)


# ---------------------------------------------------------------- while editing

def on_unfocus(changed, note, idx):
    try:
        if note.note_type()["name"] != NOTE_TYPE or note.keys()[idx] != FIELD:
            return changed
    except Exception:
        return changed
    col = mw.col
    mid, fidx = field_index(col)
    st = load_state()
    mine = core.names_in(note[FIELD]) - set(st["ignored"])
    if not mine:
        return changed
    known_elsewhere = set()
    for nid, _, flds in col.db.all("select id, mod, flds from notes where mid = ? and id != ? and flds like '%<b>%'",
                                   mid, note.id or 0):
        known_elsewhere |= core.names_in(flds.split("\x1f")[fidx])
    new = mine - known_elsewhere
    if new:
        rx = core.compile_names(new)
        run("Bold names", lambda col: apply(col, mid, fidx, rx, skip=note.id))
    return changed


# ---------------------------------------------------------------- menu

def stop_name():
    name, ok = getText("Name to stop bolding (removes the bold everywhere):")
    name = (name or "").strip()
    if not ok or not name:
        return
    col = mw.col
    mid, idx = field_index(col)
    st = load_state()
    if name not in st["ignored"]:
        st["ignored"].append(name)
    save_state(st)

    def fn(col):
        out = []
        for nid, _, flds in rows(col, mid):
            s = flds.split("\x1f")[idx]
            new = core.unbold(s, name)
            if new != s:
                n = col.get_note(nid)
                n[FIELD] = new
                out.append(n)
        return out
    run(f"Stop bolding {name}", fn)


def bold_everywhere():
    col = mw.col
    mid, idx = field_index(col)
    rx = core.compile_names(known_names(col, mid, idx, load_state()["ignored"]))
    run("Bold names", lambda col: apply(col, mid, idx, rx))


def setup_menu():
    m = QMenu("Name bold", mw)
    for label, fn in (("Bold known names in every sentence", bold_everywhere),
                      ("Stop bolding a name...", stop_name)):
        a = QAction(label, mw)
        a.triggered.connect(fn)
        m.addAction(a)
    mw.form.menuTools.addMenu(m)


gui_hooks.editor_did_unfocus_field.append(on_unfocus)
gui_hooks.profile_did_open.append(catch_up)
gui_hooks.sync_did_finish.append(catch_up)
gui_hooks.main_window_did_init.append(setup_menu)
