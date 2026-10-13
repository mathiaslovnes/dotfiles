"""
Sentence pitch

Writes a card's sentence with furigana into sentence-pitch: each word colored by its
dictionary pitch accent (the same color as that word's own card), and the pitch
contour of the whole sentence, from Suzuki-kun (OJAD), drawn above the furigana.

Runs by itself in the background (desktop): 30 seconds after Anki opens, right after
each sync, and every few minutes while something in the collection changed. Also from
Tools > Sentence pitch. Progress shows above the deck list.
Recolors a sentence when it is edited, when its card's word or category changes, or
when the category of any word in it changes on your other cards.
Does nothing for a note type until its sentence-pitch field exists.

The slow part (Yomitan, Suzuki-kun, pyopenjtalk) runs without holding the collection,
so reviewing, editing and syncing are never kept waiting; each batch of results is
written in a short step of its own, as the undo step "Sentence pitch". While you review,
or while the browser or an edit window is open, results are held and written when you're
back at the deck list, so Undo while reviewing or editing only ever undoes what you did.
"""
import json
import os
import re
import time
import traceback

from aqt import gui_hooks, mw
from aqt.operations import QueryOp
from aqt.utils import showText, tooltip
from aqt.qt import QAction, QMenu

from . import core

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.join(ADDON_DIR, "user_files")
YOMITAN_CACHE = os.path.join(USER_DIR, "yomitan_cache.json")
OJAD_CACHE = os.path.join(USER_DIR, "ojad_cache.json")
DEPS = os.path.join(USER_DIR, "word_deps.json")
REPORT_PATH = os.path.join(USER_DIR, "last_report.txt")
REDO = os.path.join(USER_DIR, "redo.json")  # {"notes": [note ids to recolor once]}
ERROR_PATH = os.path.join(USER_DIR, "last_error.txt")
BATCH = 25


def config():
    return mw.addonManager.getConfig(__name__)


def log_error(e):
    try:
        os.makedirs(USER_DIR, exist_ok=True)
        with open(ERROR_PATH, "w", encoding="utf-8") as f:
            f.write(f"{time.ctime()}\n{e!r}\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}")
    except OSError:
        pass


# ---------------------------------------------------------------- reading (with the collection, quick)

def field_index(model):
    return {f["name"]: f["ord"] for f in model["flds"]}


def read_notes(col, model):
    """[(note id, [field values])], straight from the database."""
    return [(nid, flds.split("\x1f")) for nid, flds in col.db.all(
        "select id, flds from notes where mid = ?", model["id"])]


def read_vocab(col, cfg):
    """[(word, reading, category, note type)] from your vocab cards."""
    out = []
    for v in cfg["vocab"]:
        model = col.models.by_name(v["note_type"])
        if not model:
            continue
        idx = field_index(model)
        if any(f not in idx for f in (v["word_field"], v["reading_field"], v["category_field"])):
            continue
        for _, f in read_notes(col, model):
            out.append((f[idx[v["word_field"]]], f[idx[v["reading_field"]]],
                        f[idx[v["category_field"]]], v["note_type"]))
    return out


def sentence_notes(col, cfg):
    """{note id: job} for every note with a sentence, marked stale when its colored
    sentence is missing or out of date (sentence, card word or card category changed)."""
    jobs = {}
    for spec in cfg["sentences"]:
        if not spec.get("enabled", True):
            continue
        model = col.models.by_name(spec["note_type"])
        if not model:
            continue
        idx = field_index(model)
        if any(f not in idx for f in (spec["sentence_field"], spec["word_field"], spec["pitch_field"])):
            continue

        def get(f, name):
            return f[idx[name]] if name and name in idx else ""

        for nid, f in read_notes(col, model):
            raw = get(f, spec["sentence_field"])
            if not core.clean(raw):
                continue
            if spec.get("word_mark") == "b":  # the card's word is in bold (core6k), not a name
                raw = re.sub(r"(?i)<(/?)(?:b|strong)\b[^>]*>", r"<\1i>", raw)
            job = {"nid": nid, "spec": spec, "raw": raw,
                   "written": get(f, spec.get("written_field")),
                   "word": get(f, spec["word_field"]),
                   "cat": get(f, spec.get("category_field")),
                   "reading": get(f, spec.get("reading_field")),
                   "furigana": spec.get("furigana", False)}
            h = core.source_hash(raw, job["written"], job["word"], core.first_cat(job["cat"]), job["reading"])
            stored = get(f, spec["pitch_field"])
            job["stale"] = core.stored_hash(stored) != h or core.needs_fix(stored, raw)
            jobs[nid] = job
    return jobs


def prepare(col, cfg):
    return {"notes": sentence_notes(col, cfg), "vocab": read_vocab(col, cfg)}


UNDO_NAME = "Sentence pitch"
HOLD_STATES = ("review", "overview")  # screens where Undo means "undo my last answer"
EDIT_WINDOWS = ("Browser", "EditCurrent", "AddCards")  # where Undo means "undo my edit"
HOLD_MAX = 40  # batches held back (1,000 sentences) before the worker waits for you
_held = []


def user_busy():
    """Reviewing, or the browser or an edit window is open: then Undo should only ever undo
    what you did, so nothing is written."""
    if mw.state in HOLD_STATES:
        return True
    try:
        from aqt import dialogs
        return any(dialogs._dialogs.get(name, (None, None))[1] for name in EDIT_WINDOWS)
    except Exception:
        return False


def write_notes(col, items):
    """[(note id, field, html)] -> notes changed, or None to try again later.

    Written as an undo step of its own, "Sentence pitch" (Edit > Undo Sentence pitch), and
    folded into the previous one when that was also ours, so a long run is one step. Never
    written while you review or edit (see write_now), so it doesn't come between you and
    Undo of an answer or an edit. If you undo it, the notes go back to their old version and
    get recolored on the next run."""
    status = col.undo_status()
    if status.redo:
        return None  # you just undid something: don't take away your Redo
    notes = []
    for nid, field, html in items:
        try:
            note = col.get_note(nid)
        except Exception:  # deleted meanwhile
            continue
        if field in note and note[field] != html:
            note[field] = html
            notes.append(note)
    if notes:
        step = col.add_custom_undo_entry(UNDO_NAME)
        col.update_notes(notes)
        try:
            col.merge_undo_entries(step)
            if status.undo == UNDO_NAME and status.last_step:
                col.merge_undo_entries(status.last_step)
        except Exception:  # something cleared the undo list meanwhile: the notes are saved anyway
            pass
    return len(notes)


def refresh_undo_menu(*_):
    try:
        mw.update_undo_actions()
    except Exception:
        pass


def write_later(items):
    """From the worker: hand one batch to the main thread."""
    mw.taskman.run_on_main(lambda: write_now(items))


def write_now(items, tries=0):
    """Write one batch in a short collection step of its own, unless you're reviewing or
    editing: then it waits in _held until you're back at the deck list with the browser
    and edit windows closed."""
    if not mw.col:
        return
    if user_busy():
        _held.append(items)
        return

    def done(n):
        if n is None and tries < 60:
            mw.progress.single_shot(10000, lambda: write_now(items, tries + 1), False)
        else:
            refresh_undo_menu()

    QueryOp(parent=mw, op=lambda col: write_notes(col, items), success=done) \
        .failure(log_error).run_in_background()


def flush_held(*_):
    if _held and mw.col and not user_busy():
        batches = _held[:]
        _held.clear()
        for items in batches:  # queued one after another; they end up as one undo step
            write_now(items)


# ---------------------------------------------------------------- the slow part (no collection)

def work(prep, cfg, force=False, limit=None, progress=None, write=write_later):
    """Color what needs it. -> (notes done, notes left, stats, conflicts).
    Raises core.Unavailable if Yomitan, Suzuki-kun or the analyzer can't be reached
    (batches finished before that are kept)."""
    notes = prep["notes"]
    if not notes:
        return 0, 0, {}, []
    os.makedirs(USER_DIR, exist_ok=True)
    yomitan_cache = core.load_cache(YOMITAN_CACHE)
    ojad_cache = core.load_cache(OJAD_CACHE)
    deps = {k: v for k, v in core.load_cache(DEPS).items() if int(k) in notes}
    redo = {int(x) for x in core.load_cache(REDO).get("notes", []) if int(x) in notes}
    lookup = core.Lookup(cfg["yomitan_url"], yomitan_cache)
    for card in prep["vocab"]:
        lookup.add_card(*card)
    analyzer = core.Analyzer(os.path.expanduser(cfg["python"]), os.path.join(ADDON_DIR, "analyze.py"))
    lookup.lone = (lambda w, pos: core.lone_category(analyzer, w, pos)) if cfg.get("tiebreak", True) else False
    contour = cfg.get("contour", "ojad")
    interval = cfg.get("ojad_interval_seconds", 10)
    total, done, todo = {}, 0, []

    def save():
        core.save_cache(YOMITAN_CACHE, yomitan_cache)
        core.save_cache(OJAD_CACHE, ojad_cache)
        core.save_cache(DEPS, deps)
        core.save_cache(REDO, {"notes": sorted(redo)})

    try:
        # no record of which words a sentence's colors came from (lost when Anki was
        # force-quit mid-run): recolor it, or later changes to those words wouldn't reach it
        todo = [j for j in notes.values()
                if force or j["stale"] or j["nid"] in redo or str(j["nid"]) not in deps]
        queued = {j["nid"] for j in todo}
        try:
            for k, entries in deps.items():  # a word's category changed on one of your cards
                if int(k) not in queued and core.deps_changed(lookup, entries):
                    todo.append(notes[int(k)])
        except core.Unavailable:
            if not todo:
                return 0, 0, {}, []  # Brave closed and nothing else to do: check next time
            raise
        if todo:
            lookup.ping()
        todo.sort(key=lambda j: -j["nid"])  # newest first
        if limit:
            todo = todo[:limit]
        batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
        slow = [contour == "ojad" and core.ojad_pending(b, ojad_cache, interval) > 0 for b in batches]
        per_slow, per_fast = interval + 3.0, 0.3
        for bi, batch in enumerate(batches):
            if core.stop[0]:
                break
            if progress:
                progress(done, len(todo), sum(per_slow if s else per_fast for s in slow[bi:]))
            before = (lookup.lookups, core._ojad_last[0])
            results = core.process_batch(batch, analyzer, lookup, contour, interval, ojad_cache)
            fetched = (lookup.lookups, core._ojad_last[0]) != before
            items = []
            for job, (html, stats, dep) in zip(batch, results):
                items.append((job["nid"], job["spec"]["pitch_field"], html))
                deps[str(job["nid"])] = dep
                core.merge_stats(total, stats)
            write(items)
            while len(_held) >= HOLD_MAX and not core.stop[0]:
                time.sleep(2)  # you're reviewing: wait instead of piling up results
            ids = {j["nid"] for j in batch}
            fetched = fetched or bool(redo & ids)
            redo -= ids
            if fetched:  # keep what Suzuki-kun and Yomitan returned even if Anki is force-quit
                save()
            done += len(batch)
        if progress:
            progress(done, len(todo), 0)
    finally:
        analyzer.close()
        if done or lookup.lookups:
            save()
    return done, len(todo) - done, total, lookup.conflicts()


# ---------------------------------------------------------------- status above the deck list

_status = [""]


def status_html():
    return f'<div id="sp-status" style="max-width:440px;margin:0 auto 12px;font-size:13px;opacity:.85;' \
           f'{"" if _status[0] else "display:none;"}">{_status[0]}</div>'


def set_status(text, frac=None):
    bar = ""
    if frac is not None:
        bar = ('<div style="height:3px;margin-top:5px;border-radius:2px;background:rgba(128,128,128,.35)">'
               f'<div style="height:3px;width:{max(1, round(frac * 100))}%;border-radius:2px;'
               'background:var(--blue,#89daff)"></div></div>')
    _status[0] = f"{text}{bar}" if text else ""
    if mw.state == "deckBrowser" and getattr(mw.deckBrowser, "web", None):
        mw.deckBrowser.web.eval(
            "(function(){var e=document.getElementById('sp-status');if(!e)return;"
            f"e.innerHTML={json.dumps(_status[0])};e.style.display={json.dumps('' if text else 'none')};}})()")


def on_deck_browser(deck_browser, content):
    content.tree = status_html() + content.tree


def minutes(seconds):
    m = round(seconds / 60)
    return "less than a minute" if m < 1 else f"about {m} min"


# ---------------------------------------------------------------- running it

_busy = [False]
_seen_mod = [None]  # collection state after the last run


def start(reason="", force=False, limit=None, report=False):
    cfg = config()
    if not mw.col:
        return
    if _busy[0]:
        if report:
            tooltip("Sentence pitch is already running; progress is shown above the deck list")
        return
    if not report and not cfg.get("run_in_background", True):
        return
    if reason == "timer" and (mw.col.mod == _seen_mod[0] or mw.state in HOLD_STATES):
        return  # nothing changed since the last run, or you're reviewing (answers change mod)
    _busy[0] = True
    core.stop[0] = False

    def progress(done, n, eta):
        text = f"Sentence pitch: {done:,} / {n:,} sentences · {minutes(eta)} left" if eta else \
            f"Sentence pitch: {done:,} / {n:,} sentences"
        mw.taskman.run_on_main(lambda: set_status(text, done / n if n else None))

    def finished(result):
        _busy[0] = False
        done, left, total, conflicts = result
        # after the last batch is written (same queue), remember the collection state
        QueryOp(parent=mw, op=lambda col: col.mod, success=lambda m: _seen_mod.__setitem__(0, m)) \
            .failure(log_error).run_in_background()
        if done:
            text = core.format_report(done, total, left, conflicts)
            try:
                with open(REPORT_PATH, "w", encoding="utf-8") as f:
                    f.write(text)
            except OSError:
                pass
            set_status(f"Sentence pitch: {done:,} sentences colored" + (f", {left:,} left" if left else ""))
            mw.progress.single_shot(15000, lambda: set_status("") if not _busy[0] else None, False)
            if report:
                showText(text, title="Sentence pitch")
        else:
            set_status("")
            if report:
                tooltip("Sentence pitch: everything is up to date")

    def failed(e):
        _busy[0] = False
        if isinstance(e, core.Unavailable):
            if str(e) != "stopped":
                set_status(f"Sentence pitch: paused, {e}. It continues by itself later.")
        else:
            log_error(e)
            set_status("Sentence pitch: stopped by an error (user_files/last_error.txt)")
        if report and not (isinstance(e, core.Unavailable) and str(e) == "stopped"):
            showText(f"Sentence pitch stopped. Sentences finished before this point are saved.\n\n{e}",
                     title="Sentence pitch")

    def prepared(prep):
        if not prep["notes"]:
            finished((0, 0, {}, []))
            return
        QueryOp(parent=mw, op=lambda _: work(prep, cfg, force, limit, progress), success=finished) \
            .failure(failed).without_collection().run_in_background()

    QueryOp(parent=mw, op=lambda col: prepare(col, cfg), success=prepared).failure(failed).run_in_background()


_timer = [None]
_flush_timer = [None]


CSS_START = "/* ---------- Sentence pitch (add-on) ---------- */"
CSS_END = ".sp .kifuku    { color: var(--purple); }"


def sync_styling(cfg):
    """Keep the add-on's block in each sentence note type's Styling the same as card.css
    (only where the block is already there), so it always fits the HTML this version writes."""
    try:
        with open(os.path.join(ADDON_DIR, "card.css"), encoding="utf-8") as f:
            block = f.read().strip()
    except OSError:
        return
    for spec in cfg["sentences"]:
        model = mw.col.models.by_name(spec["note_type"])
        css = model["css"] if model else ""
        if css.count(CSS_START) != 1 or css.count(CSS_END) != 1:
            continue
        a, b = css.index(CSS_START), css.index(CSS_END) + len(CSS_END)
        if css[a:b] != block:
            model["css"] = css[:a] + block + css[b:]
            mw.col.models.update_dict(model)


def on_profile_open():
    try:
        sync_styling(config())
    except Exception as e:
        log_error(e)
    minutes_ = config().get("background_every_minutes", 5)
    if minutes_ and _timer[0] is None:
        _timer[0] = mw.progress.timer(int(minutes_ * 60 * 1000), lambda: start("timer"), True, parent=mw)
    if _flush_timer[0] is None:  # writes held while you reviewed or edited go out when you're done
        _flush_timer[0] = mw.progress.timer(3000, flush_held, True, parent=mw)
    mw.progress.single_shot(30 * 1000, lambda: start("open"))


def on_profile_close():
    core.stop[0] = True  # the worker stops before its next Suzuki-kun request or batch


# ---------------------------------------------------------------- menu

def show_report():
    try:
        with open(REPORT_PATH, encoding="utf-8") as f:
            showText(f.read(), title="Sentence pitch")
    except OSError:
        tooltip("No report yet")


def setup_menu():
    menu = QMenu("Sentence pitch", mw)
    for label, fn in (("Test: color the 20 newest sentences", lambda: start("menu", limit=20, report=True)),
                      ("Color new and changed sentences", lambda: start("menu", report=True)),
                      ("Recolor all sentences", lambda: start("menu", force=True, report=True)),
                      ("Show last report", show_report)):
        action = QAction(label, mw)
        action.triggered.connect(fn)
        menu.addAction(action)
    mw.form.menuTools.addMenu(menu)


gui_hooks.sync_did_finish.append(lambda: start("sync"))
gui_hooks.profile_did_open.append(on_profile_open)
gui_hooks.profile_will_close.append(on_profile_close)
gui_hooks.deck_browser_will_render_content.append(on_deck_browser)
gui_hooks.state_did_change.append(flush_held)
setup_menu()
