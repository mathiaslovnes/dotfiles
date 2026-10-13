#!/usr/bin/env python3
"""
Replace the word audio on old Anki notes with the first recording from the
Local Audio Server (NHK16 > Shinmeikai 8 > Forvo > JapanesePod101).

The previous audio is copied into OLD_FIELD, so every change can be undone:
set REVERT = True to put the old audio back on all migrated notes.
Notes that already have something in OLD_FIELD are treated as done and skipped.

Needs Anki open (AnkiConnect + Local Audio Server). The browser is not needed.
"""

import base64
import html
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request

# ---------------- config ----------------
NOTE_TYPE = "subs2srs"
WORD_FIELD = "wordDictionaryForm"
READING_FIELD = "reading"
AUDIO_FIELD = "wordAudio"
OLD_FIELD = "word-audio-old"
DRY_RUN = False
LIMIT = None  # only process this many notes; None = all
REVERT = False  # True: undo, i.e. move OLD_FIELD back into AUDIO_FIELD
# ----------------------------------------

ANKI_URL = "http://127.0.0.1:8765"
LOCAL_AUDIO_URL = "http://127.0.0.1:5050"
EMPTY_MARK = "(empty)"  # stored in OLD_FIELD when the note had no audio before
SAMPLE_DIR = "audio_samples"


def post(url, payload, timeout=120):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def anki(action, **params):
    """AnkiConnect call. Anki sometimes stalls under a long run of writes, so wait
    and retry a few times before giving up."""
    for attempt in range(4):
        try:
            res = post(
                ANKI_URL, {"action": action, "version": 6, "params": params}, timeout=60
            )
            break
        except (TimeoutError, OSError) as e:
            if attempt == 3:
                raise SystemExit(
                    f"\nAnki stopped responding ({e}).\nRestart Anki (Cmd+Q, reopen) and run the "
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


def sound_file(s):
    m = re.search(r"\[sound:([^\]]+)\]", s or "")
    return m.group(1) if m else ""


def query_readings(s):
    """Readings to try with the audio server, from the note's pitch-HTML reading field.
    Turns nasal か゚ back into が. The field repeats the reading once per pitch
    dictionary (よむよむ), so the collapsed form is tried too, but only after the
    full one, because real words can repeat (はは, いろいろ)."""
    s = re.sub(r"[(（][^)）]*only[)）]", "", s)
    s = re.sub(r"[\s、,・]", "", s)
    s = unicodedata.normalize("NFD", s)
    s = re.sub("([かきくけこカキクケコ])\u309a", "\\1\u3099", s)
    s = unicodedata.normalize("NFC", s)
    out = [s]
    for p in range(1, len(s) // 2 + 1):
        if len(s) % p == 0 and s == s[:p] * (len(s) // p):
            out.append(s[:p])
            break
    return out


def pick_audio(word, reading):
    """Ask the local audio server directly. Return (filename, base64 content, source, reason)."""
    sources = []
    for rd in query_readings(reading):
        q = urllib.parse.urlencode({"term": word, "reading": rd})
        with urllib.request.urlopen(f"{LOCAL_AUDIO_URL}/?{q}", timeout=30) as r:
            sources = json.loads(r.read().decode()).get("audioSources", [])
        if sources:
            break
    if not sources:
        return None, None, None, "no audio found"
    first = sources[0]
    url = first["url"]
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path).strip("/")
    parts = path.split("/")
    # nhk16/audio/2018….mp3 -> local_nhk16_2018….mp3 ; forvo/user/読む.mp3 -> local_forvo_user_読む.mp3
    fname = "local_" + "_".join(
        [parts[0]] + parts[2:] if parts[1] in ("audio", "media") else parts
    )
    # Forvo files are named after the word (forvo/user/在る.mp3): percent-encode the path
    u = urllib.parse.urlparse(url)
    safe_url = u._replace(
        path=urllib.parse.quote(urllib.parse.unquote(u.path))
    ).geturl()
    with urllib.request.urlopen(safe_url, timeout=30) as r:
        data = base64.b64encode(r.read()).decode()
    return fname, data, first.get("name", parts[0]), "ok"


def note_ids():
    ids = anki("findNotes", query=f'"note:{NOTE_TYPE}"')
    if not ids:
        raise SystemExit(f"No notes found for note type '{NOTE_TYPE}'")
    first = anki("notesInfo", notes=ids[:1])[0]["fields"]
    missing = [
        f for f in (WORD_FIELD, READING_FIELD, AUDIO_FIELD, OLD_FIELD) if f not in first
    ]
    if missing:
        raise SystemExit(
            f"Field(s) not found: {missing}\nAvailable fields: {list(first)}"
        )
    return ids


def write(updates, quiet=False):
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
        if not quiet:
            print(f"  wrote {min(i + 25, len(updates))}/{len(updates)}")
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
                        {AUDIO_FIELD: "" if old == EMPTY_MARK else old, OLD_FIELD: ""},
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
    plan, skipped, done, stored = [], [], 0, set()
    if DRY_RUN:
        os.makedirs(SAMPLE_DIR, exist_ok=True)
    else:
        # Write mp3s straight into Anki's media folder: going through AnkiConnect's
        # storeMediaFile thousands of times exhausts Anki's open-file limit.
        media_dir = anki("getMediaDirPath")
    pending, written = [], 0

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
            old_raw = f[AUDIO_FIELD]["value"]
            if not word:
                skipped.append(f"(empty word)\t\tempty word field")
                continue
            try:
                fname, content, source, reason = pick_audio(word, reading)
            except Exception as e:
                skipped.append(f"{word}\t{reading}\tERROR: {e}")
                continue
            if not fname:
                skipped.append(f"{word}\t{reading}\t{reason}")
                continue
            if fname == sound_file(old_raw):
                skipped.append(f"{word}\t{reading}\tsame audio as before")
                continue

            if DRY_RUN:
                if len(plan) < 10:
                    tag = re.sub(r"[^\w]+", "_", source.split()[0])
                    with open(
                        os.path.join(
                            SAMPLE_DIR, f"{len(plan) + 1:02d}_{word}_{tag}.mp3"
                        ),
                        "wb",
                    ) as fh:
                        fh.write(base64.b64decode(content))
            elif fname not in stored:
                path = os.path.join(media_dir, fname)
                if not os.path.exists(
                    path
                ):  # reuse files from an earlier, interrupted run
                    with open(path, "wb") as fh:
                        fh.write(base64.b64decode(content))
                stored.add(fname)
            fields = {
                AUDIO_FIELD: f"[sound:{fname}]",
                OLD_FIELD: old_raw.strip() or EMPTY_MARK,
            }
            plan.append(
                (n["noteId"], word, sound_file(old_raw), f"{fname}  [{source}]", fields)
            )
            pending.append((n["noteId"], fields))
        # Save every chunk, so an interruption never loses finished work
        if not DRY_RUN and pending:
            write(pending, quiet=True)
            written += len(pending)
            pending = []
        print(
            f"  checked {min(i + 200, len(ids))}/{len(ids)} notes"
            + ("" if DRY_RUN else f", {written} updated")
        )

    with open("audio_changes.tsv", "w", encoding="utf-8") as fh:
        fh.write("\n".join(f"{w}\t{o}\t{nf}" for _, w, o, nf, _ in plan))
    with open("audio_skipped.tsv", "w", encoding="utf-8") as fh:
        fh.write("\n".join(skipped))

    reasons = {}
    for line in skipped:
        k = line.rsplit("\t", 1)[-1].split(":")[0]
        reasons[k] = reasons.get(k, 0) + 1
    print(
        f"\n{done} notes checked: {len(plan)} get new audio, {len(skipped)} unchanged"
    )
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  unchanged, {k}: {v}")
    print("Full lists: audio_changes.tsv, audio_skipped.tsv")

    if DRY_RUN:
        print(
            f"\nDRY RUN - the first {min(10, len(plan))} new recordings are saved in ./{SAMPLE_DIR}/ to listen to."
        )
        for _, word, old, new, _ in plan[:15]:
            print(f"  {word}: {old or '(none)'} -> {new}")
        print("\nSet DRY_RUN = False and run again to write.")
        return

    print("Done.")


if __name__ == "__main__":
    main()
