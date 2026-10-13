#!/usr/bin/env python3
"""
Backfill the pitch-accent category on old Anki notes,
using the Yomitan API (browser open) and AnkiConnect (Anki open).

Only fills fields that are empty. Never overwrites existing content.
Run with DRY_RUN = True first and check the sample output.
"""

import html
import json
import re
import unicodedata
import urllib.request

# ---------------- config ----------------
NOTE_TYPE = "core6k"  # exact name from Tools > Manage Note Types
WORD_FIELD = "Vocabulary-Kanji"
READING_FIELD = "Vocabulary-Kana"
CATEGORY_FIELD = "pitch-accent-category"  # the field holding heiban / kifuku / ...
DRY_RUN = False
LIMIT = None  # only check this many notes without a category; None = all
# ----------------------------------------

ANKI_URL = "http://127.0.0.1:8765"
YOMITAN_URL = "http://127.0.0.1:19633/ankiFields"
MARKERS = ["expression", "reading", "pitch-accent-categories"]


def post(url, payload, timeout=60):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def anki(action, **params):
    res = post(ANKI_URL, {"action": action, "version": 6, "params": params})
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {res['error']}")
    return res["result"]


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def to_hira(s):
    """Normalize a reading for comparison: katakana -> hiragana, and drop voicing
    marks, because the pitch HTML in the reading field writes nasal が as か + ゜."""
    s = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if c not in "\u3099\u309a\u309b\u309c")


def lookup(word):
    res = post(
        YOMITAN_URL,
        {
            "text": word,
            "type": "term",
            "markers": MARKERS,
            "maxEntries": 10,
            "includeMedia": False,
        },
    )
    return res.get("fields", [])


def norm_reading(s):
    """Plain, comparable reading from the note's pitch-HTML reading field.
    Drops '(X only)' disambiguation notes, whitespace and list separators."""
    s = re.sub(r"[(（][^)）]*only[)）]", "", s)
    s = re.sub(r"[\s、,・]", "", s)
    return to_hira(s)


def is_kana(s):
    return bool(s) and all(
        "ぁ" <= c <= "ゖ" or "ァ" <= c <= "ヺ" or c == "ー" for c in s
    )


def reading_matches(note_r, entry_r):
    """True if the note's reading is the entry's reading, possibly repeated:
    the pitch field shows the reading once per pitch dictionary."""
    if not note_r or not entry_r:
        return False
    k, rem = divmod(len(note_r), len(entry_r))
    return rem == 0 and note_r == entry_r * k


def pick(entries, word, reading):
    """Return (category, reason). category is None when no safe answer exists."""
    note_r = norm_reading(reading)

    cands = [e for e in entries if clean(e.get("expression")) == word]
    if is_kana(word):
        # A kana-only card can mean any word with that reading (それ: the
        # interjection [1] and 其れ "that" [0]), so consider all of them;
        # if they disagree, the note is skipped as ambiguous.
        w = to_hira(word)
        cands += [
            e
            for e in entries
            if e not in cands and norm_reading(clean(e.get("reading"))) == w
        ]
    if not cands:
        return None, "no matching entry"

    if note_r:
        by_reading = [
            e
            for e in cands
            if reading_matches(note_r, norm_reading(clean(e.get("reading"))))
        ]
        if not by_reading:
            return None, "reading mismatch"
        cands = by_reading

    cats = {clean(e.get("pitch-accent-categories")) for e in cands} - {""}
    if not cats:
        return None, "no pitch data"
    if len(cats) > 1:
        return None, "ambiguous: " + "/".join(sorted(cats))
    return cats.pop(), "ok"


def main():
    # All notes of the type, filtered here: Anki's "field:" search misses fields
    # that only look empty (a stray <br> or &nbsp; left by the editor).
    all_ids = anki("findNotes", query=f'"note:{NOTE_TYPE}"')
    if not all_ids:
        print(f"No notes found for note type '{NOTE_TYPE}'")
        return

    first = anki("notesInfo", notes=all_ids[:1])[0]["fields"]
    missing = [f for f in (WORD_FIELD, READING_FIELD, CATEGORY_FIELD) if f not in first]
    if missing:
        print(f"Field(s) not found on this note type: {missing}")
        print(f"Available fields: {list(first)}")
        return

    updates, skipped, done = [], [], 0
    for i in range(0, len(all_ids), 200):
        if LIMIT is not None and done >= LIMIT:
            break
        for n in anki("notesInfo", notes=all_ids[i : i + 200]):
            f = n["fields"]
            if clean(f[CATEGORY_FIELD]["value"]):
                continue  # already has a category
            if LIMIT is not None and done >= LIMIT:
                break
            done += 1
            word = clean(f[WORD_FIELD]["value"])
            reading = clean(f[READING_FIELD]["value"])
            if not word:
                skipped.append(f"(empty word)\t{reading}\tempty word field")
                continue
            try:
                cat, reason = pick(lookup(word), word, reading)
            except Exception as e:
                skipped.append(f"{word}\t{reading}\tERROR: {e}")
                continue
            if cat:
                updates.append((n["noteId"], word, reading, {CATEGORY_FIELD: cat}))
            else:
                skipped.append(f"{word}\t{reading}\t{reason}")
        print(f"  checked {min(i + 200, len(all_ids))}/{len(all_ids)} notes")

    with open("planned_changes.tsv", "w", encoding="utf-8") as fh:
        fh.write(
            "\n".join(f"{w}\t{r}\t{new[CATEGORY_FIELD]}" for _, w, r, new in updates)
        )
    with open("skipped.tsv", "w", encoding="utf-8") as fh:
        fh.write("\n".join(skipped))

    reasons = {}
    for line in skipped:
        key = line.rsplit("\t", 1)[-1].split(":")[0]
        reasons[key] = reasons.get(key, 0) + 1
    print(
        f"\n{done} notes without a category: {len(updates)} to fill, {len(skipped)} skipped"
    )
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  skipped, {k}: {v}")
    print("Full lists: planned_changes.tsv, skipped.tsv")

    if DRY_RUN:
        print("\nDRY RUN - sample of changes:")
        for _, word, reading, new in updates[:30]:
            print(f"  {word} ({reading}): {new[CATEGORY_FIELD]}")
        print("\nSet DRY_RUN = False and run again to write.")
        return

    for i in range(0, len(updates), 100):
        batch = updates[i : i + 100]
        actions = [
            {
                "action": "updateNoteFields",
                "params": {"note": {"id": nid, "fields": new}},
            }
            for nid, _, _, new in batch
        ]
        results = anki("multi", actions=actions)
        errors = [r for r in results if isinstance(r, dict) and r.get("error")]
        if errors:
            print(f"  {len(errors)} errors in batch starting at {i}: {errors[0]}")
        print(f"  wrote {min(i + 100, len(updates))}/{len(updates)}")
    print("Done.")


if __name__ == "__main__":
    main()
