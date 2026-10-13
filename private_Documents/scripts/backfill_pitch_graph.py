#!/usr/bin/env python3
"""
Replace the pitch-accent graph on Core 6k notes with Yomitan's graph, from the
same dictionary and the same entry matching as pitch-accent-category, so the
graph and the word color on a card always agree.

The previous graph is copied into OLD_FIELD first; REVERT = True puts it back.
Notes that already have something in OLD_FIELD are treated as done and skipped.
Notes where the matching is unsure (ambiguous kana, no pitch data, ...) keep
their current graph.

Needs Anki (AnkiConnect) and the browser (Yomitan API) open.
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
DRY_RUN = False
LIMIT = None  # only process this many notes; None = all
REVERT = False  # True: undo, i.e. move OLD_FIELD back into GRAPH_FIELD
# ----------------------------------------

ANKI_URL = "http://127.0.0.1:8765"
YOMITAN_URL = "http://127.0.0.1:19633/ankiFields"
MARKERS = ["expression", "reading", "pitch-accent-categories", "pitch-accent-graphs"]
EMPTY_MARK = "(empty)"


def post(url, payload, timeout=60):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def anki(action, **params):
    """AnkiConnect call, with a few retries in case Anki stalls."""
    for attempt in range(4):
        try:
            res = post(ANKI_URL, {"action": action, "version": 6, "params": params})
            break
        except (TimeoutError, OSError) as e:
            if attempt == 3:
                raise SystemExit(
                    f"\nAnki stopped responding ({e}).\nRestart Anki and run the "
                    f"script again: notes already updated are kept and skipped."
                )
            print(
                f"  Anki not responding, waiting {15 * (attempt + 1)}s and retrying..."
            )
            time.sleep(15 * (attempt + 1))
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {res['error']}")
    return res["result"]


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def to_hira(s):
    s = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if c not in "゙゚゛゜")


def norm_reading(s):
    s = re.sub(r"[(（][^)）]*only[)）]", "", s)
    s = re.sub(r"[\s、,・]", "", s)
    return to_hira(s)


def is_kana(s):
    return bool(s) and all(
        "ぁ" <= c <= "ゖ" or "ァ" <= c <= "ヺ" or c == "ー" for c in s
    )


def reading_matches(note_r, entry_r):
    if not note_r or not entry_r:
        return False
    k, rem = divmod(len(note_r), len(entry_r))
    return rem == 0 and note_r == entry_r * k


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


def pick_graph(entries, word, reading):
    """Same matching as the category backfill. Return (graph html, reason)."""
    note_r = norm_reading(reading)
    cands = [e for e in entries if clean(e.get("expression")) == word]
    if is_kana(word):
        w = to_hira(word)
        cands += [
            e
            for e in entries
            if e not in cands and norm_reading(clean(e.get("reading"))) == w
        ]
    if not cands:
        return None, "no matching entry"
    if note_r:
        cands = [
            e
            for e in cands
            if reading_matches(note_r, norm_reading(clean(e.get("reading"))))
        ]
        if not cands:
            return None, "reading mismatch"
    # Only entries that actually have pitch data draw an <svg> graph
    with_graph = [e for e in cands if "<svg" in (e.get("pitch-accent-graphs") or "")]
    if not with_graph:
        return None, "no pitch data"
    cats = {clean(e.get("pitch-accent-categories")) for e in with_graph} - {""}
    if len(cats) > 1:
        return None, "ambiguous: " + "/".join(sorted(cats))
    return with_graph[0]["pitch-accent-graphs"].strip(), "ok"


def note_ids():
    ids = anki("findNotes", query=f'"note:{NOTE_TYPE}"')
    if not ids:
        raise SystemExit(f"No notes found for note type '{NOTE_TYPE}'")
    first = anki("notesInfo", notes=ids[:1])[0]["fields"]
    missing = [
        f for f in (WORD_FIELD, READING_FIELD, GRAPH_FIELD, OLD_FIELD) if f not in first
    ]
    if missing:
        raise SystemExit(
            f"Field(s) not found: {missing}\nAvailable fields: {list(first)}"
        )
    return ids


def write(updates):
    for i in range(0, len(updates), 25):
        batch = updates[i : i + 25]
        results = anki(
            "multi",
            actions=[
                {
                    "action": "updateNoteFields",
                    "params": {"note": {"id": nid, "fields": fields}},
                }
                for nid, fields in batch
            ],
        )
        errors = [r for r in results if isinstance(r, dict) and r.get("error")]
        if errors:
            print(f"  {len(errors)} errors in batch starting at {i}: {errors[0]}")
        time.sleep(0.2)


def revert():
    updates = []
    ids = note_ids()
    for i in range(0, len(ids), 200):
        for n in anki("notesInfo", notes=ids[i : i + 200]):
            old = n["fields"][OLD_FIELD]["value"].strip()
            if old:
                updates.append(
                    (
                        n["noteId"],
                        {GRAPH_FIELD: "" if old == EMPTY_MARK else old, OLD_FIELD: ""},
                    )
                )
    print(f"{len(updates)} notes to revert")
    if DRY_RUN:
        print("DRY RUN - set DRY_RUN = False to revert.")
        return
    write(updates)
    print("Done.")


def main():
    if REVERT:
        return revert()

    ids = note_ids()
    plan, skipped, done, pending, written, samples = [], [], 0, [], 0, []
    for i in range(0, len(ids), 200):
        if LIMIT is not None and done >= LIMIT:
            break
        for n in anki("notesInfo", notes=ids[i : i + 200]):
            f = n["fields"]
            if f[OLD_FIELD]["value"].strip():
                continue  # already migrated
            if LIMIT is not None and done >= LIMIT:
                break
            done += 1
            word = clean(f[WORD_FIELD]["value"])
            reading = clean(f[READING_FIELD]["value"])
            old_raw = f[GRAPH_FIELD]["value"]
            if not word:
                skipped.append(f"(empty word)\t{reading}\tempty word field")
                continue
            try:
                graph, reason = pick_graph(lookup(word), word, reading)
            except Exception as e:
                skipped.append(f"{word}\t{reading}\tERROR: {e}")
                continue
            if not graph:
                skipped.append(f"{word}\t{reading}\t{reason}")
                continue
            if graph == old_raw.strip():
                skipped.append(f"{word}\t{reading}\tsame graph as before")
                continue
            fields = {GRAPH_FIELD: graph, OLD_FIELD: old_raw.strip() or EMPTY_MARK}
            plan.append((word, reading))
            if len(samples) < 30:
                samples.append((word, reading, old_raw, graph))
            pending.append((n["noteId"], fields))
        if not DRY_RUN and pending:
            write(pending)
            written += len(pending)
            pending = []
        print(
            f"  checked {min(i + 200, len(ids))}/{len(ids)} notes"
            + ("" if DRY_RUN else f", {written} updated")
        )

    with open("graph_changes.tsv", "w", encoding="utf-8") as fh:
        fh.write("\n".join(f"{w}\t{r}" for w, r in plan))
    with open("graph_skipped.tsv", "w", encoding="utf-8") as fh:
        fh.write("\n".join(skipped))

    reasons = {}
    for line in skipped:
        k = line.rsplit("\t", 1)[-1].split(":")[0]
        reasons[k] = reasons.get(k, 0) + 1
    print(
        f"\n{done} notes checked: {len(plan)} get Yomitan's graph, {len(skipped)} keep their current one"
    )
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  kept, {k}: {v}")
    print("Full lists: graph_changes.tsv, graph_skipped.tsv")
    if DRY_RUN:
        write_preview(samples)
        print(
            "\nDRY RUN - open graph_preview.html to compare old and new graphs "
            "(macOS: open graph_preview.html)."
        )
        print("Set DRY_RUN = False and run again to write.")
        return
    print("Done.")


def write_preview(samples):
    rows = "\n".join(
        f"<tr><td class='w'>{html.escape(w)}<div class='r'>{html.escape(r)}</div></td>"
        f"<td>{old or '<span class=r>(empty)</span>'}</td><td>{new}</td></tr>"
        for w, r, old, new in samples
    )
    page = f"""<!doctype html><meta charset='utf-8'><title>Pitch graph preview</title>
<style>
body {{ background: #222; color: #fff; font-family: 'Hiragino Mincho ProN', serif; padding: 24px; }}
table {{ border-collapse: collapse; }}
th, td {{ border-bottom: 1px solid #444; padding: 10px 20px; text-align: left; vertical-align: middle; }}
th {{ font-family: sans-serif; font-size: 13px; color: #aaa; font-weight: normal; }}
.w {{ font-size: 26px; }} .r {{ font-size: 14px; color: #aaa; }}
svg > path {{ stroke: #fff !important; }} svg > circle[r="5"] {{ fill: #fff !important; }}
</style>
<table><tr><th>word</th><th>old graph (add-on)</th><th>new graph (Yomitan)</th></tr>
{rows}
</table>"""
    with open("graph_preview.html", "w", encoding="utf-8") as fh:
        fh.write(page)


if __name__ == "__main__":
    main()
