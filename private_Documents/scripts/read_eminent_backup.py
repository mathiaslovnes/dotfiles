#!/usr/bin/env python3
"""
Read the Eminent V2.4 note type out of an Anki backup WITHOUT touching your
collection: its front/back templates, its styling, and which notes had
four-by-three-aspect-ratio filled (note ids survive Change Note Type).

Usage:  python3 read_eminent_backup.py
It goes through the backups newest first and uses the first one that still
contains Eminent V2.4 with notes. Output goes to ./eminent_export/.
Needs Python 3.14+ (built-in zstd) or the `zstandard` package or the `zstd` tool.
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import zipfile

BACKUP_DIR = os.path.expanduser("~/Library/Application Support/Anki2/user 1/backups")
NOTE_TYPE = "Eminent V2.4"
FLAG_FIELD = "four-by-three-aspect-ratio"
OUT_DIR = "eminent_export"


def zstd_decompress(data):
    try:
        from compression import zstd  # Python 3.14+

        return zstd.decompress(data)
    except ImportError:
        pass
    try:
        import zstandard

        return zstandard.ZstdDecompressor().decompressobj().decompress(data)
    except ImportError:
        pass
    try:
        return subprocess.run(
            ["zstd", "-d", "-c"], input=data, capture_output=True, check=True
        ).stdout
    except FileNotFoundError:
        sys.exit(
            "Need zstd support: use Python 3.14+, `pip install zstandard`, or `brew install zstd`."
        )


def extract_collection(colpkg, tmpdir):
    with zipfile.ZipFile(colpkg) as z:
        names = z.namelist()
        if "collection.anki21b" in names:
            data = zstd_decompress(z.read("collection.anki21b"))
        elif "collection.anki21" in names:
            data = z.read("collection.anki21")
        else:
            data = z.read("collection.anki2")
    path = os.path.join(tmpdir, "col.db")
    with open(path, "wb") as fh:
        fh.write(data)
    return path


# --- minimal protobuf reader (modern Anki stores templates/CSS as protobuf) ---
def read_varint(b, i):
    shift = result = 0
    while True:
        byte = b[i]
        i += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, i
        shift += 7


def proto_fields(b):
    """field number -> list of raw values (bytes for length-delimited, int otherwise)."""
    out, i = {}, 0
    while i < len(b):
        key, i = read_varint(b, i)
        num, wt = key >> 3, key & 7
        if wt == 0:
            val, i = read_varint(b, i)
        elif wt == 1:
            val, i = b[i : i + 8], i + 8
        elif wt == 2:
            ln, i = read_varint(b, i)
            val, i = b[i : i + ln], i + ln
        elif wt == 5:
            val, i = b[i : i + 4], i + 4
        else:
            break
        out.setdefault(num, []).append(val)
    return out


def text(fields, num):
    v = fields.get(num)
    return v[0].decode("utf-8", "replace") if v else ""


def read_notetype(db):
    con = sqlite3.connect(db)
    # Anki's own case-insensitive collation on name columns; plain SQLite lacks it
    con.create_collation(
        "unicase",
        lambda a, b: (a.casefold() > b.casefold()) - (a.casefold() < b.casefold()),
    )
    tables = {
        r[0] for r in con.execute("select name from sqlite_master where type='table'")
    }
    if "notetypes" in tables:  # modern schema
        row = con.execute(
            "select id, config from notetypes where name = ?", (NOTE_TYPE,)
        ).fetchone()
        if not row:
            return None
        ntid, cfg = row
        css = text(proto_fields(cfg), 3)
        tmpls = [
            (name, text(proto_fields(c), 1), text(proto_fields(c), 2))
            for name, c in con.execute(
                "select name, config from templates where ntid = ? order by ord",
                (ntid,),
            )
        ]
        fields = [
            r[0]
            for r in con.execute(
                "select name from fields where ntid = ? order by ord", (ntid,)
            )
        ]
    else:  # legacy schema: everything in col.models (JSON)
        models = json.loads(con.execute("select models from col").fetchone()[0])
        m = next((m for m in models.values() if m["name"] == NOTE_TYPE), None)
        if not m:
            return None
        ntid, css = int(m["id"]), m["css"]
        tmpls = [(t["name"], t["qfmt"], t["afmt"]) for t in m["tmpls"]]
        fields = [f["name"] for f in m["flds"]]
    notes = con.execute("select id, flds from notes where mid = ?", (ntid,)).fetchall()
    return {"css": css, "templates": tmpls, "fields": fields, "notes": notes}


def main():
    backups = sorted(
        (
            os.path.join(BACKUP_DIR, f)
            for f in os.listdir(BACKUP_DIR)
            if f.endswith((".colpkg", ".apkg"))
        ),
        key=os.path.getmtime,
        reverse=True,
    )
    if not backups:
        sys.exit(f"No backups found in {BACKUP_DIR}")
    for bk in backups:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                nt = read_notetype(extract_collection(bk, tmp))
            except Exception as e:
                print(f"  {os.path.basename(bk)}: could not read ({e})")
                continue
        if nt and nt["notes"]:
            break
        print(f"  {os.path.basename(bk)}: no {NOTE_TYPE} notes, trying an older one")
    else:
        sys.exit(f"No backup with {NOTE_TYPE} notes found.")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "styling.css"), "w", encoding="utf-8") as fh:
        fh.write(nt["css"])
    for name, front, back in nt["templates"]:
        safe = "".join(c if c.isalnum() else "_" for c in name)
        with open(
            os.path.join(OUT_DIR, f"{safe}_front.html"), "w", encoding="utf-8"
        ) as fh:
            fh.write(front)
        with open(
            os.path.join(OUT_DIR, f"{safe}_back.html"), "w", encoding="utf-8"
        ) as fh:
            fh.write(back)

    flagged = []
    if FLAG_FIELD in nt["fields"]:
        idx, word_idx = nt["fields"].index(FLAG_FIELD), 0
        for nid, flds in nt["notes"]:
            vals = flds.split("\x1f")
            if idx < len(vals) and vals[idx].strip():
                flagged.append(f"{nid}\t{vals[word_idx]}\t{vals[idx]}")
    with open(
        os.path.join(OUT_DIR, "four_by_three_notes.tsv"), "w", encoding="utf-8"
    ) as fh:
        fh.write("\n".join(flagged))

    print(
        f"Read from {os.path.basename(bk)}: {len(nt['notes'])} {NOTE_TYPE} notes, "
        f"{len(flagged)} with {FLAG_FIELD} filled"
    )
    print(f"Wrote templates, styling.css and four_by_three_notes.tsv to ./{OUT_DIR}/")


if __name__ == "__main__":
    main()
