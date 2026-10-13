#!/usr/bin/env python3
"""
Crop the screenshots of the former Eminent V2.4 notes to what Eminent showed:
centered, full height, 16:9 (4:3 for the 90 notes that had four-by-three-aspect-ratio).
No template, field or tag changes.

Safety:
  - The cropped image is saved under a NEW name (…_crop.webp). The original file is
    never modified or deleted; it stays in the media folder until you run
    Check Media -> Delete Unused yourself.
  - Every change is appended to crop_log.tsv (note id, old picture field, new picture field)
    BEFORE the next note is touched, so a crash leaves an accurate log.
  - MODE = "revert" puts the old picture field back on every note in the log
    (only if the field still holds what this script wrote, so later edits are kept).
  - Reruns skip pictures that are already cropped or already the right shape.

Which notes were Eminent is read from the backup made before the conversion, with
read_eminent_backup.py: keep both files in the same folder.
Needs Anki open (AnkiConnect) and Pillow (run with ~/.venvs/anki/bin/python).
"""

import json
import os
import re
import tempfile
import time
import urllib.request

from PIL import Image, ImageDraw

import read_eminent_backup as backup

# ---------------- config ----------------
NOTE_TYPE = "subs2srs"
PICTURE_FIELD = "picture"
MODE = "crop"  # "dry-run", "crop" or "revert"
LIMIT = None  # crop at most this many pictures; None = all
# ----------------------------------------

ANKI_URL = "http://127.0.0.1:8765"
LOG_FILE = "crop_log.tsv"
SHEET_DIR = "crop_review"


def anki(action, **params):
    req = urllib.request.Request(
        ANKI_URL,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode(),
        headers={"Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                res = json.loads(r.read().decode())
            break
        except (TimeoutError, OSError) as e:
            if attempt == 3:
                raise SystemExit(
                    f"\nAnki stopped responding ({e}). Restart Anki and run again; "
                    "the log is up to date, so a rerun continues where it stopped."
                )
            time.sleep(15 * (attempt + 1))
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {res['error']}")
    return res["result"]


def eminent_notes():
    """{note id: is_4x3} from the newest backup that still has Eminent notes."""
    files = sorted(
        (
            os.path.join(backup.BACKUP_DIR, f)
            for f in os.listdir(backup.BACKUP_DIR)
            if f.endswith(".colpkg")
        ),
        key=os.path.getmtime,
        reverse=True,
    )
    for bk in files:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                nt = backup.read_notetype(backup.extract_collection(bk, tmp))
            except Exception:
                continue
        if nt and nt["notes"]:
            idx = nt["fields"].index(backup.FLAG_FIELD)
            print(f"Using {os.path.basename(bk)}")
            out = {}
            for nid, flds in nt["notes"]:
                vals = flds.split("\x1f")
                out[nid] = idx < len(vals) and bool(vals[idx].strip())
            return out
    raise SystemExit("No backup with Eminent notes found.")


def center_box(w, h, ratio):
    """Centered crop of the given width/height ratio, full height (full width if the image is narrower)."""
    if w / h > ratio:
        nw = round(h * ratio)
        x = (w - nw) // 2
        return (x, 0, x + nw, h)
    nh = round(w / ratio)
    y = (h - nh) // 2
    return (0, y, w, y + nh)


def contact_sheets(items):
    """items: (label, image path, crop box). Red box = what is kept. 24 per page."""
    os.makedirs(SHEET_DIR, exist_ok=True)
    for old in os.listdir(SHEET_DIR):
        if old.startswith("sheet_"):
            os.remove(os.path.join(SHEET_DIR, old))
    tw, th, cols = 320, 160, 4
    for page in range(0, len(items), 24):
        chunk = items[page : page + 24]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new(
            "RGB", (cols * (tw + 10) + 10, rows * (th + 34) + 10), (40, 40, 40)
        )
        draw = ImageDraw.Draw(sheet)
        for k, (label, path, box) in enumerate(chunk):
            im = Image.open(path)
            scale = min(tw / im.width, th / im.height)
            thumb = im.convert("RGB")
            thumb.thumbnail((tw, th), reducing_gap=2.0)
            x, y = 10 + (k % cols) * (tw + 10), 10 + (k // cols) * (th + 34)
            sheet.paste(thumb, (x, y))
            draw.rectangle(
                [
                    x + box[0] * scale,
                    y + box[1] * scale,
                    x + box[2] * scale - 1,
                    y + box[3] * scale - 1,
                ],
                outline=(255, 60, 60),
                width=2,
            )
            draw.text((x, y + th + 4), label[:56], fill=(230, 230, 230))
        sheet.save(
            os.path.join(SHEET_DIR, f"sheet_{page // 24 + 1:03d}.jpg"), quality=85
        )


def revert():
    if not os.path.exists(LOG_FILE):
        raise SystemExit(f"No {LOG_FILE} here, nothing to revert.")
    entries = {}
    with open(LOG_FILE, encoding="utf-8") as fh:
        for line in fh:
            nid, old, new = line.rstrip("\n").split("\t")
            entries[int(nid)] = (
                json.loads(old),
                json.loads(new),
            )  # last entry per note wins
    ids = list(entries)
    restored, changed_since = 0, []
    for i in range(0, len(ids), 200):
        for n in anki("notesInfo", notes=ids[i : i + 200]):
            if not n or "noteId" not in n:
                continue
            old, new = entries[n["noteId"]]
            if n["fields"][PICTURE_FIELD]["value"] != new:
                changed_since.append(str(n["noteId"]))
                continue
            anki(
                "updateNoteFields",
                note={"id": n["noteId"], "fields": {PICTURE_FIELD: old}},
            )
            restored += 1
    print(f"Restored {restored} picture fields.")
    if changed_since:
        print(
            f"{len(changed_since)} left alone because the field was edited after cropping: "
            + ", ".join(changed_since[:20])
            + (" …" if len(changed_since) > 20 else "")
        )
    os.rename(LOG_FILE, LOG_FILE + f".reverted-{int(time.time())}")
    print("The _crop files are now unused; Check Media -> Delete Unused removes them.")


def main():
    if MODE == "revert":
        return revert()
    if MODE not in ("dry-run", "crop"):
        raise SystemExit('MODE must be "dry-run", "crop" or "revert"')

    flagged = eminent_notes()
    ids = list(flagged)
    media = anki("getMediaDirPath")
    log = open(LOG_FILE, "a", encoding="utf-8") if MODE == "crop" else None

    todo, skipped, done = [], {}, 0

    def skip(why):
        skipped[why] = skipped.get(why, 0) + 1

    for i in range(0, len(ids), 200):
        for n in anki("notesInfo", notes=ids[i : i + 200]):
            if LIMIT is not None and done >= LIMIT:
                break
            if not n or n.get("modelName") != NOTE_TYPE:
                skip(f"not a {NOTE_TYPE} note any more")
                continue
            field = n["fields"].get(PICTURE_FIELD, {}).get("value", "")
            m = re.search(r'src="([^"]+)"', field)
            if not m:
                skip("no picture")
                continue
            name = m.group(1)
            if "_crop." in name:
                skip("already cropped")
                continue
            path = os.path.join(media, name)
            if not os.path.exists(path):
                skip("picture file missing")
                continue
            img = Image.open(path)
            four_by_three = flagged[n["noteId"]]
            box = center_box(img.width, img.height, 4 / 3 if four_by_three else 16 / 9)
            if box == (0, 0, img.width, img.height):
                skip("already the right shape")
                continue
            done += 1
            word = re.sub(
                r"<[^>]+>",
                "",
                n["fields"].get("wordDictionaryForm", {}).get("value", ""),
            )
            todo.append(
                (
                    f"{n['noteId']} {'4:3' if four_by_three else '16:9'} {word}",
                    path,
                    box,
                )
            )
            if MODE == "dry-run":
                continue
            stem, ext = os.path.splitext(name)
            new_name = f"{stem}_crop{ext}"
            kw = {"quality": 90} if ext.lower() in (".webp", ".jpg", ".jpeg") else {}
            img.crop(box).save(os.path.join(media, new_name), **kw)
            new_field = field.replace(name, new_name)
            log.write(
                f"{n['noteId']}\t{json.dumps(field, ensure_ascii=False)}\t"
                f"{json.dumps(new_field, ensure_ascii=False)}\n"
            )
            log.flush()
            anki(
                "updateNoteFields",
                note={"id": n["noteId"], "fields": {PICTURE_FIELD: new_field}},
            )
            time.sleep(0.05)
        print(
            f"  checked {min(i + 200, len(ids))}/{len(ids)}, {done} {'to crop' if MODE == 'dry-run' else 'cropped'}"
        )

    if log:
        log.close()
    n43 = sum(1 for label, _, _ in todo if " 4:3 " in label)
    print(
        f"\n{done} pictures {'to crop' if MODE == 'dry-run' else 'cropped'} "
        f"({done - n43} to 16:9, {n43} to 4:3)"
    )
    for k, v in skipped.items():
        print(f"  skipped, {k}: {v}")
    if MODE == "dry-run":
        contact_sheets(todo)
        print(
            f"\nDRY RUN - every picture is in ./{SHEET_DIR}/ (red box = what is kept). "
            'Set MODE = "crop" to crop.'
        )
    else:
        print(f'Log: {LOG_FILE}. To undo: MODE = "revert".')


if __name__ == "__main__":
    main()
