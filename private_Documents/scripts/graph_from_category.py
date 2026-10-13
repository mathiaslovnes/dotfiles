#!/usr/bin/env python3
"""
For Core 6k cards whose category you set by hand: replace the old add-on graph
(or fill an emptied one) with a graph drawn in exactly Yomitan's format, from the
card's reading and the drop position its category implies (heiban 0, atamadaka 1,
odaka = number of morae; nakadaka with 4+ morae and kifuku take the position from
the matching Yomitan entries). Cards that already have a Yomitan graph are left alone.

The old graph is backed up in OLD_FIELD (if not already backed up).
Run with DRY_RUN = True first. Needs Anki (AnkiConnect) and Brave (Yomitan API) open.
"""

import html
import json
import re
import time
import unicodedata
import urllib.request

# ---------------- config ----------------
NOTE_TYPE = "core6k"
WORD_FIELD = "Vocabulary-Kanji"
READING_FIELD = "Vocabulary-Kana"
GRAPH_FIELD = "pitch-accent"
OLD_FIELD = "pitch-accent-old"
CATEGORY_FIELD = "pitch-accent-category"
DRY_RUN = False
# ----------------------------------------

ANKI_URL = "http://127.0.0.1:8765"
YOMITAN_URL = "http://127.0.0.1:19633/ankiFields"
MARKERS = [
    "expression",
    "reading",
    "pitch-accent-categories",
    "pitch-accent-graphs",
    "pitch-accent-positions",
]
EMPTY_MARK = "(empty)"
CATEGORIES = {"heiban", "atamadaka", "nakadaka", "odaka", "kifuku"}


def post(url, payload, timeout=60):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def anki(action, **params):
    for attempt in range(4):
        try:
            res = post(ANKI_URL, {"action": action, "version": 6, "params": params})
            break
        except (TimeoutError, OSError) as e:
            if attempt == 3:
                raise SystemExit(
                    f"\nAnki stopped responding ({e}). Restart Anki and run again."
                )
            time.sleep(15 * (attempt + 1))
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {res['error']}")
    return res["result"]


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def exact_reading(s):
    """Hiragana reading keeping voicing (ふる != ぶる); nasal か゚ becomes が."""
    s = re.sub(r"[(（][^)）]*only[)）]", "", s)
    s = re.sub(r"[\s、,・]", "", s)
    s = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
    s = unicodedata.normalize("NFD", s)
    s = re.sub("([かきくけこ])\u309a", "\\1\u3099", s)
    return unicodedata.normalize("NFC", s)


def is_kana(s):
    return bool(s) and all(
        "ぁ" <= c <= "ゖ" or "ァ" <= c <= "ヺ" or c == "ー" for c in s
    )


def is_yomitan_graph(s):
    return "1.5em" in (s or "")


SMALL_KANA = set("ゃゅょぁぃぅぇぉゎャュョァィゥェォヮ")


def split_morae(reading):
    morae = []
    for c in reading:
        if c in SMALL_KANA and morae:
            morae[-1] += c
        else:
            morae.append(c)
    return morae


def is_high(i, pos):
    """Yomitan's rule for whether mora i is high, given the drop position."""
    if pos == 0:
        return i > 0
    if pos == 1:
        return i < 1
    return 0 < i < pos


def draw_graph(n, pos):
    """The pitch graph in exactly Yomitan's SVG format: n morae + the particle."""
    style = 'style="fill:none;stroke-width:5;stroke:currentColor;"'
    xs = [25 + 50 * i for i in range(n + 1)]
    ys = [25 if is_high(i, pos) else 75 for i in range(n + 1)]
    parts = []
    if n > 1:
        pts = " L".join(f"{xs[i]} {ys[i]}" for i in range(n))
        parts.append(f'<path d="M{pts}" {style}></path>')
    parts.append(
        f'<path d="M{xs[n - 1]} {ys[n - 1]} L{xs[n]} {ys[n]}" '
        'style="fill:none;stroke-width:5;stroke:currentColor;stroke-dasharray:5 5;"></path>'
    )
    for i in range(n):
        if i == pos - 1:  # the mora the pitch drops after
            parts.append(
                f'<circle cx="{xs[i]}" cy="{ys[i]}" r="15" {style}></circle>'
                f'<circle cx="{xs[i]}" cy="{ys[i]}" r="5" style="fill:currentColor;"></circle>'
            )
        else:
            parts.append(
                f'<circle cx="{xs[i]}" cy="{ys[i]}" r="15" '
                'style="stroke-width:5;fill:currentColor;stroke:currentColor;"></circle>'
            )
    parts.append(
        f'<path d="M0 13 L15 -13 L-15 -13 Z" transform="translate({xs[n]},{ys[n]})" {style}></path>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" focusable="false" viewBox="0 0 {50 * (n + 1)} 100" '
        'style="display:inline-block;vertical-align:middle;height:1.5em;">'
        + "".join(parts)
        + "</svg>"
    )


def first_position(s):
    m = re.search(r"\d+", clean(s or ""))
    return int(m.group()) if m else None


def position_for(word, reading, category, n):
    """Drop position for the card's category. Returns (position, source, problem)."""
    if category == "heiban":
        return 0, "heiban", None
    if category == "atamadaka":
        return 1, "atamadaka", None
    if category == "odaka":
        return n, "odaka", None
    if category == "nakadaka" and n == 3:
        return 2, "nakadaka, 3 morae", None
    # nakadaka with 4+ morae, or kifuku: take the position from the matching entries
    entries = post(
        YOMITAN_URL,
        {
            "text": word,
            "type": "term",
            "markers": MARKERS,
            "maxEntries": 10,
            "includeMedia": False,
        },
    ).get("fields", [])
    r = exact_reading(reading)
    found = set()
    for e in entries:
        er = exact_reading(clean(e.get("reading")))
        same_word = clean(e.get("expression")) == word
        kana_match = is_kana(word) and er == exact_reading(word)
        if (
            (same_word or kana_match)
            and (not r or er == r)
            and clean(e.get("pitch-accent-categories")) == category
        ):
            p = first_position(e.get("pitch-accent-positions"))
            if p is not None:
                found.add(p)
    if not found:
        return (
            None,
            None,
            f"no Yomitan entry with {category} to take the drop position from",
        )
    if len(found) > 1:
        return None, None, f"entries disagree on the drop position ({sorted(found)})"
    p = found.pop()
    return p, f"{category} [{p}] from Yomitan", None


def main():
    ids = anki("findNotes", query=f'"note:{NOTE_TYPE}"')
    rows, updates = [], []
    for i in range(0, len(ids), 200):
        for n in anki("notesInfo", notes=ids[i : i + 200]):
            f = n["fields"]
            cat = clean(f[CATEGORY_FIELD]["value"])
            if not cat or is_yomitan_graph(f[GRAPH_FIELD]["value"]):
                continue  # no category set yet, or already a Yomitan graph
            word = clean(f[WORD_FIELD]["value"])
            reading = clean(f[READING_FIELD]["value"])
            if cat not in CATEGORIES:
                rows.append(
                    f"  {word} {reading}: category '{cat}' is misspelled, skipped"
                )
                continue
            nm = len(split_morae(exact_reading(reading)))
            if nm == 0:
                rows.append(f"  {word}: empty reading, graph left as is")
                continue
            try:
                pos, entry, problem = position_for(word, reading, cat, nm)
            except Exception as e:
                rows.append(f"  {word} {reading}: ERROR {e}")
                continue
            if pos is None:
                rows.append(f"  {word} {reading}: {problem}, graph left as is")
                continue
            graph = draw_graph(nm, pos)
            fields = {GRAPH_FIELD: graph}
            if not f[OLD_FIELD]["value"].strip():
                fields[OLD_FIELD] = f[GRAPH_FIELD]["value"].strip() or EMPTY_MARK
            rows.append(
                f"  {word} {reading}: drew {entry} graph, drop after mora {pos} of {nm}"
            )
            updates.append((n["noteId"], fields))

    print("\n".join(rows))
    print(f"\n{len(updates)} graphs to update, {len(rows) - len(updates)} kept")
    if DRY_RUN:
        print("DRY RUN - set DRY_RUN = False and run again to write.")
        return
    for j in range(0, len(updates), 25):
        anki(
            "multi",
            actions=[
                {
                    "action": "updateNoteFields",
                    "params": {"note": {"id": nid, "fields": fields}},
                }
                for nid, fields in updates[j : j + 25]
            ],
        )
    print("Done.")


if __name__ == "__main__":
    main()
