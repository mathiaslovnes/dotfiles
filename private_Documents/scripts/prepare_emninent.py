#!/usr/bin/env python3
"""
Prepare Eminent notes for conversion to subs2srs.

Before running: add two fields to the Eminent note type, named exactly
`sentence` and `wordAsWritten` (Tools > Manage Note Types > Eminent > Fields > Add).

The script fills them on every Eminent note:
  sentence      = before-sentence + cloze-prefix + cloze-body + cloze-suffix + after-sentence
  wordAsWritten = cloze-body (as plain text)
and reports how many notes use the fields that subs2srs doesn't have.
Notes whose `sentence` is already filled are left alone.
"""

import html
import json
import re
import urllib.request

# ---------------- config ----------------
NOTE_TYPE = "Eminent V2.4"
DRY_RUN = False
# ----------------------------------------

ANKI_URL = "http://127.0.0.1:8765"
DROPPED = ["four-by-three-aspect-ratio"]


def anki(action, **params):
    req = urllib.request.Request(
        ANKI_URL,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read().decode())
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {res['error']}")
    return res["result"]


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def tidy(s):
    """Remove left-to-right marks from subtitle text and collapse runs of
    spaces (where subtitle lines were joined) into a single space."""
    s = re.sub("[‎‏]", "", s)
    s = re.sub(r"(?:[ \t\r\n ]|&nbsp;)+", " ", s)
    return s.strip()


def main():
    ids = anki("findNotes", query=f'"note:{NOTE_TYPE}"')
    print(f"{len(ids)} {NOTE_TYPE} notes")
    if not ids:
        return
    first = anki("notesInfo", notes=ids[:1])[0]["fields"]
    missing = [
        f
        for f in (
            "sentence",
            "wordAsWritten",
            "cloze-prefix",
            "cloze-body",
            "cloze-suffix",
        )
        if f not in first
    ]
    if missing:
        raise SystemExit(
            f"Field(s) not found: {missing}\nAdd them to the note type first. "
            f"Available fields: {list(first)}"
        )

    updates, no_cloze, already = [], [], 0
    used = {f: [] for f in DROPPED if f in first}
    for i in range(0, len(ids), 200):
        for n in anki("notesInfo", notes=ids[i : i + 200]):
            f = n["fields"]
            word = clean(f.get("wordDictionaryForm", {}).get("value", ""))
            for name in used:
                if clean(f[name]["value"]):
                    used[name].append(word)
            if clean(f["sentence"]["value"]):
                already += 1
                continue
            before, pre, body, suf, after = (
                f.get(k, {}).get("value", "")
                for k in (
                    "before-sentence",
                    "cloze-prefix",
                    "cloze-body",
                    "cloze-suffix",
                    "after-sentence",
                )
            )
            if not clean(before + pre + body + suf + after):
                no_cloze.append(word)
                continue
            updates.append(
                (
                    n["noteId"],
                    word,
                    # body as plain text: the subs2srs template highlights the word itself
                    {
                        "sentence": tidy(before + pre + clean(body) + suf + after),
                        "wordAsWritten": tidy(clean(body)),
                    },
                )
            )

    print(
        f"{len(updates)} notes to fill, {already} already filled, "
        f"{len(no_cloze)} with no sentence at all"
    )
    if no_cloze:
        print(
            f"  no sentence: {', '.join(no_cloze[:20])}{' ...' if len(no_cloze) > 20 else ''}"
        )
    for name, words in used.items():
        print(
            f"'{name}' is filled on {len(words)} notes"
            + (f", e.g. {', '.join(words[:10])}" if words else "")
        )

    if DRY_RUN:
        print("\nDRY RUN - sample:")
        for _, word, new in updates[:15]:
            print(f"  {word}: [{new['wordAsWritten']}]  {clean(new['sentence'])}")
        print("\nSet DRY_RUN = False and run again to write.")
        return

    for i in range(0, len(updates), 100):
        batch = updates[i : i + 100]
        results = anki(
            "multi",
            actions=[
                {
                    "action": "updateNoteFields",
                    "params": {"note": {"id": nid, "fields": new}},
                }
                for nid, _, new in batch
            ],
        )
        errors = [r for r in results if isinstance(r, dict) and r.get("error")]
        if errors:
            print(f"  {len(errors)} errors in batch starting at {i}: {errors[0]}")
        print(f"  wrote {min(i + 100, len(updates))}/{len(updates)}")
    print("Done.")


if __name__ == "__main__":
    main()
