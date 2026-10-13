"""
Note type export

Writes every note type's templates, styling and field names as plain files to
~/Library/Application Support/Anki2/note-types/<note type>/, so they can be kept in
dotfiles (chezmoi). Runs when Anki opens, after each sync, and whenever a note type is
changed. A file is only rewritten when its content changed. The folder mirrors Anki:
the folder of a note type you delete, and the files of a template you rename or delete,
are removed (only files this add-on writes; anything else you put there stays).
"""
import os
import re

from aqt import gui_hooks, mw

OWN = ("styling.css", "fields.txt", ".front.html", ".back.html")


def out_dir():
    return os.path.join(mw.pm.base, "note-types")


def safe(name):
    return re.sub(r'[/\\:*?"<>|]', "_", name).strip() or "_"


def write(path, text):
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return
    except OSError:
        pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def export():
    if not mw.col:
        return
    root = out_dir()
    keep = {}  # folder -> files written for it
    for m in mw.col.models.all():
        name = safe(m["name"])
        files = {"styling.css": m["css"], "fields.txt": "".join(f["name"] + "\n" for f in m["flds"])}
        for t in m["tmpls"]:
            files[f"{safe(t['name'])}.front.html"] = t["qfmt"]
            files[f"{safe(t['name'])}.back.html"] = t["afmt"]
        os.makedirs(os.path.join(root, name), exist_ok=True)
        for f, text in files.items():
            write(os.path.join(root, name, f), text)
        keep.setdefault(name, set()).update(files)
    for name in os.listdir(root):  # what Anki no longer has
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(OWN) and f not in keep.get(name, ()):
                os.remove(os.path.join(d, f))
        if name not in keep and not [f for f in os.listdir(d) if f != ".DS_Store"]:
            if os.path.exists(os.path.join(d, ".DS_Store")):
                os.remove(os.path.join(d, ".DS_Store"))
            os.rmdir(d)


def safe_export(*_):
    try:
        export()
    except Exception as e:  # never get in the way of Anki
        print("note type export:", e)


def on_operation(changes, handler):
    if getattr(changes, "notetype", False):
        safe_export()


gui_hooks.profile_did_open.append(safe_export)
gui_hooks.sync_did_finish.append(safe_export)
gui_hooks.operation_did_execute.append(on_operation)
