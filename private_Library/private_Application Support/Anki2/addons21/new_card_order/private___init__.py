"""
New card order

Orders your new sentence cards so the most frequent words come first, in sentences you can
follow: by the frequency of each card's word (the freq number on the card) and of the other
words in its sentence you haven't met yet. When a sentence contains a word another new card
teaches, that card comes first, at least one day's worth of new cards earlier.

Runs by itself: when Anki opens (right after its sync, if it syncs on open), after each sync,
when Sentence pitch has read new cards, and every 10 minutes when something changed.
Tools > New card order > Show order explains the order. The words of each sentence come from
the Sentence pitch add-on (its word_deps.json). Ranks are the freq-harmonic-mean number:
the card's own field, and for other words the same number from Yomitan (Brave open).
"""
import html
import json
import os
import re
import statistics
import time
import traceback
import urllib.request

from aqt import gui_hooks, mw
from aqt.operations import QueryOp
from aqt.qt import QAction, QMenu
from aqt.utils import showText, tooltip

from . import order

ADDON = os.path.dirname(os.path.abspath(__file__))
USER = os.path.join(ADDON, "user_files")
FREQ_CACHE = os.path.join(USER, "freq_cache.json")
REPORT = os.path.join(USER, "last_order.txt")
ERROR = os.path.join(USER, "last_error.txt")
UNDO_NAME = "New card order"
NO_FREQ = 9999999  # what the Yomitan template gives a word without frequency data
HOLD_STATES = ("review", "overview")
EDIT_WINDOWS = ("Browser", "EditCurrent", "AddCards")


def config():
    return mw.addonManager.getConfig(__name__)


def log_error(e):
    try:
        os.makedirs(USER, exist_ok=True)
        with open(ERROR, "w", encoding="utf-8") as f:
            f.write(f"{time.ctime()}\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}")
    except OSError:
        pass


# ---------------------------------------------------------------- words

def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).replace("\xa0", " ").strip()


def to_hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s or "")


def is_kana(s):
    return bool(s) and all("ぁ" <= c <= "ゖ" or "ァ" <= c <= "ヺ" or c == "ー" for c in s)


def word_key(word):
    """One key per word: its spelling, or for a word in kana its hiragana (ヤツ = やつ)."""
    return "k:" + to_hira(word) if is_kana(word) else word


def field_reading(value):
    """The reading in a reading field; the pitch HTML repeats it once per dictionary."""
    s = re.sub(r"[(（][^)）]*[)）]|[\s、,・/]", "", clean(value))
    s = to_hira(s)
    for n in range(1, len(s) // 2 + 1):
        if len(s) % n == 0 and s == s[:n] * (len(s) // n):
            return s[:n]
    return s


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(path + ".tmp", path)


class Unavailable(Exception):
    pass


class Ranks:
    """Frequency rank of a word, as Yomitan's frequency-harmonic-rank-custom template gives it
    (the number in the freq field of your cards). Cached in user_files/freq_cache.json."""

    def __init__(self, url, unranked):
        self.url = url.rstrip("/") + "/ankiFields"
        self.unranked = unranked
        self.cache = load_json(FREQ_CACHE, {})
        self.asked = 0

    def lookup(self, word, reading=None):
        k = f"{word}\t{reading or ''}"
        if k not in self.cache:
            payload = {"text": word, "type": "term", "maxEntries": 10, "includeMedia": False,
                       "markers": ["expression", "reading", "frequency-harmonic-rank-custom"]}
            try:
                req = urllib.request.Request(self.url, data=json.dumps(payload).encode(),
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    entries = json.loads(r.read().decode()).get("fields", [])
            except Exception as e:
                raise Unavailable(f"Yomitan isn't answering ({e}). Is Brave open?")
            self.asked += 1
            cands = [e for e in entries if clean(e.get("expression")) == word]
            if not cands and is_kana(word):
                cands = [e for e in entries if to_hira(clean(e.get("reading"))) == to_hira(word)]
            if reading:
                cands = [e for e in cands if to_hira(clean(e.get("reading"))) == reading] or cands
            value = None
            for e in cands:
                m = re.search(r"\d+", clean(e.get("frequency-harmonic-rank-custom")))
                if m and int(m.group()) < NO_FREQ:
                    value = int(m.group())
                    break
            self.cache[k] = value
        return self.cache[k]

    def get(self, word, reading=None):
        v = self.lookup(word, reading)
        return v if v is not None else self.unranked

    def save(self):
        if self.asked:
            save_json(FREQ_CACHE, self.cache)


# ---------------------------------------------------------------- reading the collection (quick)

def prepare(col, cfg):
    """New cards to order, which words you already know, and how many new cards make a day."""
    new_cards, known_targets, reviewed_nids, ordered_mids = [], set(), set(), []
    for name, spec in cfg["note_types"].items():
        model = col.models.by_name(name)
        if not model:
            continue
        idx = {f["name"]: f["ord"] for f in model["flds"]}
        if spec["word_field"] not in idx:
            continue
        ordered = spec.get("order", False)
        if ordered:
            ordered_mids.append(model["id"])
        notes = {nid: flds.split("\x1f") for nid, flds in col.db.all(
            "select id, flds from notes where mid = ?", model["id"])}
        for cid, nid, ctype, queue, due in col.db.all(
                "select c.id, c.nid, c.type, c.queue, c.due from cards c join notes n on c.nid = n.id "
                "where n.mid = ?", model["id"]):
            f = notes[nid]
            word = clean(f[idx[spec["word_field"]]])
            if not word:
                continue
            if ctype != 0:
                reviewed_nids.add(nid)
                known_targets.add(word_key(word))
            elif ordered and queue != -1:
                reading = field_reading(f[idx[spec["reading_field"]]]) if spec.get("reading_field") in idx else ""
                freq = clean(f[idx[spec["freq_field"]]]) if spec.get("freq_field") in idx else ""
                sentence = clean(f[idx[spec["sentence_field"]]]) if spec.get("sentence_field") in idx else ""
                new_cards.append({"cid": cid, "nid": nid, "key": word_key(word), "word": word,
                                  "reading": reading, "freq": int(freq) if freq.isdigit() else None, "due": due,
                                  "group": sentence or f"note {nid}"})
    one_day = cfg.get("one_day", "auto")
    how = "set in the add-on's config"
    if not isinstance(one_day, int) or one_day < 1:
        one_day, how = learned_per_day(col, ordered_mids)
    return {"cards": new_cards, "known_targets": known_targets, "reviewed": reviewed_nids,
            "one_day": one_day, "one_day_how": how, "mod": col.mod}


def learned_per_day(col, mids):
    """How many new cards you learn on a study day: the median over your last 30 such days."""
    if not mids:
        return 25, "default"
    marks = ",".join("?" * len(mids))
    rows = col.db.all(f"select min(r.id) from revlog r join cards c on r.cid = c.id join notes n on c.nid = n.id "
                      f"where n.mid in ({marks}) group by r.cid", *mids)
    cutoff = (col.sched.day_cutoff - 86400 * 400) * 1000
    days = {}
    for (ms,) in rows:
        if ms and ms > cutoff:
            d = (ms // 1000 - col.sched.day_cutoff) // 86400
            days[d] = days.get(d, 0) + 1
    recent = [days[d] for d in sorted(days)[-30:]]
    if not recent:
        return 25, "default"
    return max(1, round(statistics.median(recent))), f"the median of your last {len(recent)} study days"


# ---------------------------------------------------------------- the slow part (no collection)

def deps_path(cfg):
    p = cfg.get("word_deps", "")
    return os.path.expanduser(p) if p else os.path.join(
        mw.addonManager.addonsFolder(), "sentence_pitch", "user_files", "word_deps.json")


def work(prep, cfg, path):
    """-> (card ids in order, text of the report)"""
    raw = load_json(path, {})
    reading_of, deps = {}, {}
    for nid, entries in raw.items():
        keys = []
        for e in entries:
            if e and e[0]:
                k = word_key(e[0])
                keys.append(k)
                reading_of.setdefault(k, (e[0], e[1] or None))
        deps[int(nid)] = keys
    kana_forms = {}  # the words of a sentence's cards, as the sentence may write them in kana
    for c in prep["cards"]:  # (おぼつかない for 覚束ない): not extra unknown words
        if c["reading"]:
            kana_forms.setdefault(c["group"], set()).add("k:" + c["reading"])
    for c in prep["cards"]:
        drop = kana_forms.get(c["group"], set()) - {c["key"]}
        if drop and c["nid"] in deps:
            deps[c["nid"]] = [k for k in deps[c["nid"]] if k not in drop]
    known = set(prep["known_targets"])
    for nid in prep["reviewed"]:
        known.update(deps.get(nid, ()))
    ranks = Ranks(cfg.get("yomitan_url", "http://127.0.0.1:19633"), cfg.get("unranked", 50000))
    try:
        cards = []
        for c in prep["cards"]:
            r = c["freq"] if c["freq"] and c["freq"] < NO_FREQ else ranks.get(c["word"], c["reading"] or None)
            cards.append(dict(c, rank=r))
        words = {}
        for c in cards:
            reading_of.setdefault(c["key"], (c["word"], c["reading"] or None))
            words[c["key"]] = c["rank"]

        def rank(k):
            if k not in words:
                w, r = reading_of.get(k, (k[2:] if k.startswith("k:") else k, None))
                words[k] = ranks.get(w, r)
            return words[k]

        ids, info, summary = order.build(cards, deps, known, rank, cfg.get("rule", "average"), prep["one_day"])
    finally:
        ranks.save()
    names = {k: w for k, (w, _) in reading_of.items()}
    return ids, report(cards, info, summary, prep, cfg, ids, names)


def report(cards, info, summary, prep, cfg, ids, names):
    by_id = {c["cid"]: c for c in cards}

    def name(k):
        return names.get(k, k[2:] if k.startswith("k:") else k)

    n = prep["one_day"]
    rule = "the most common unknown word" if cfg.get("rule") == "most_common" else \
        "the average of the unknown words (never better than the card's own word)"
    out = [f"New card order: {len(ids):,} new cards, by {rule}.",
           f"One day = {n} new cards ({prep['one_day_how']}).",
           f"{summary['waiting']} cards contain a word another new card teaches; they come after it.",
           f"{summary['shared']} sentences have more than one card; those cards come a day apart."]
    if summary["short"]:
        out.append(f"{len(summary['short'])} cards come less than a day after what they wait for: "
                   "nothing else was left to fill the gap (marked below).")
    elif summary["waiting"] or summary["shared"]:
        out.append("All of them keep at least a day's distance.")
    if summary["cycles"]:
        out.append(f"{summary['cycles']} times cards needed each other's words: the more frequent one went first.")
    for pos, cid in enumerate(ids):
        if pos % n == 0:
            out.append(f"\nDay {pos // n + 1}")
        c, d = by_id[cid], info[cid]
        extra = [f"{name(k)} {r:,}" for k, r in sorted(d["unknown"].items(), key=lambda x: x[1])]
        after = [f"after {name(k)} (#{t + 1})" for k, t in sorted(d["after"].items(), key=lambda x: x[1] or 0)
                 if t is not None and t < pos]
        if d["sibling"] is not None:
            after.append(f"same sentence as #{d['sibling'] + 1}")
        if after and not d["gap_ok"]:
            after.append("less than a day")
        line = f"{pos + 1:5}  {c['word']}  freq {c['rank']:,}  score {round(d['s']):,}"
        if d["e"] < d["s"]:
            line += f"  (moved up: a better card needs it)"
        if extra:
            line += "  unknown: " + ", ".join(extra)
        if after:
            line += "  " + ", ".join(after)
        out.append(line)
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- writing (with the collection, quick)

def user_busy():
    if mw.state in HOLD_STATES:
        return True
    try:
        from aqt import dialogs
        return any(dialogs._dialogs.get(name, (None, None))[1] for name in EDIT_WINDOWS)
    except Exception:
        return False


def write_order(col, ids):
    """Give the cards positions in this order (from the lowest position they have now).
    -> cards moved, 0 if already in this order, None if you just undid something."""
    if not ids:
        return 0
    marks = ",".join("?" * len(ids))
    rows = col.db.all(f"select id, due from cards where id in ({marks}) and type = 0", *ids)
    due = dict(rows)
    ids = [i for i in ids if i in due]
    if [i for i, _ in sorted(rows, key=lambda r: (r[1], r[0]))] == ids:
        return 0
    status = col.undo_status()
    if status.redo:
        return None
    step = col.add_custom_undo_entry(UNDO_NAME)
    col.sched.reposition_new_cards(ids, min(due.values()), 1, False, False)
    try:
        col.merge_undo_entries(step)
    except Exception:
        pass
    return len(ids)


_pending = [None]
_busy = [False]
_seen = [None]  # (collection mod, word_deps.json mtime) of the last run
_again = [False, False]  # run once more when this run ends (and show the report then)
_closing = [False]


def flush(*_):
    ids = _pending[0]
    if ids is None or not mw.col or _closing[0] or user_busy():
        return
    _pending[0] = None

    def done(n):
        if n is None:
            _pending[0] = ids  # Redo is waiting: try again later
        elif n:
            tooltip(f"New card order: {n:,} new cards reordered")
        try:
            mw.update_undo_actions()
        except Exception:
            pass

    QueryOp(parent=mw, op=lambda col: write_order(col, ids), success=done).failure(log_error).run_in_background()


def start(reason="", report_after=False):
    cfg = config()
    if not mw.col or _closing[0]:
        return
    if _busy[0]:
        if reason != "timer":  # a sync or new word list during a run: run again right after it
            _again[0] = True
            _again[1] = _again[1] or report_after
        return
    path = deps_path(cfg)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = None
    if reason == "timer" and _seen[0] == (mw.col.mod, mtime):
        return
    _busy[0] = True

    def prepared(prep):
        if _closing[0]:
            _busy[0] = False
            return

        def finished(result):
            _busy[0] = False
            _seen[0] = (prep["mod"], mtime)
            ids, text = result
            try:
                os.makedirs(USER, exist_ok=True)
                with open(REPORT, "w", encoding="utf-8") as f:
                    f.write(text)
            except OSError:
                pass
            _pending[0] = ids
            flush()
            if report_after:
                showText(text, title="New card order")
            run_again()

        def failed(e):
            _busy[0] = False
            _seen[0] = (None, mtime)  # Yomitan closed: try again on the 10-minute timer, not every few seconds
            if not isinstance(e, Unavailable):
                log_error(e)
            if report_after:
                showText(f"New card order stopped:\n\n{e}", title="New card order")
            run_again()

        QueryOp(parent=mw, op=lambda _: work(prep, cfg, path), success=finished) \
            .failure(failed).without_collection().run_in_background()

    def failed(e):
        _busy[0] = False
        log_error(e)
        run_again()

    QueryOp(parent=mw, op=lambda col: prepare(col, cfg), success=prepared).failure(failed).run_in_background()


def run_again():
    if _again[0] and not _closing[0]:
        report = _again[1]
        _again[0] = _again[1] = False
        start("again", report_after=report)


def watch_deps():
    """sentence-pitch rewrote its word list (new cards it has read): order again right away."""
    if not mw.col or _closing[0] or _seen[0] is None:
        return
    try:
        mtime = os.path.getmtime(deps_path(config()))
    except OSError:
        return
    if mtime != _seen[0][1]:
        start("deps")


def show_order():
    try:
        with open(REPORT, encoding="utf-8") as f:
            showText(f.read(), title="New card order")
    except OSError:
        tooltip("No order yet")


_timers = []


def on_profile_open():
    _closing[0] = False
    if not _timers:
        _timers.append(mw.progress.timer(10 * 60 * 1000, lambda: start("timer"), True, parent=mw))
        _timers.append(mw.progress.timer(5000, flush, True, parent=mw))
        _timers.append(mw.progress.timer(15 * 1000, watch_deps, True, parent=mw))
    try:
        sync_follows = mw.can_auto_sync()
    except Exception:
        sync_follows = False
    if not sync_follows:  # with sync on open, the run starts the moment that sync is done
        mw.progress.single_shot(0, lambda: start("open"))


def on_profile_close():
    _closing[0] = True  # Anki syncs while closing: don't start a run then
    _pending[0] = None


def setup_menu():
    menu = QMenu("New card order", mw)
    for label, fn in (("Reorder now", lambda: start("menu", report_after=True)), ("Show order", show_order)):
        a = QAction(label, mw)
        a.triggered.connect(fn)
        menu.addAction(a)
    mw.form.menuTools.addMenu(menu)


gui_hooks.profile_did_open.append(on_profile_open)
gui_hooks.profile_will_close.append(on_profile_close)
gui_hooks.sync_did_finish.append(lambda: start("sync"))
setup_menu()
