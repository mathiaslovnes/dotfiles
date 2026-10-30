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
A run you start from Tools > Sentence pitch is written right away, also while you review
(the card on screen is redrawn); it only waits while the browser or an edit window is
open, since saving there would write over it. Its report lists the sentences that changed.
"""
import json
import os
from html.parser import HTMLParser
import re
import time
import traceback

from aqt import gui_hooks, mw
from aqt.operations import QueryOp
from aqt.utils import askUser, showText, tooltip
from aqt.qt import QAction, QKeySequence, QMenu

from . import core

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.join(ADDON_DIR, "user_files")
YOMITAN_CACHE = os.path.join(USER_DIR, "yomitan_cache.json")
OJAD_CACHE = os.path.join(USER_DIR, "ojad_cache.json")
DEPS = os.path.join(USER_DIR, "word_deps.json")
REPORT_PATH = os.path.join(USER_DIR, "last_report.txt")
REDO = os.path.join(USER_DIR, "redo.json")  # {"notes": [note ids to recolor once]}
REDO_NEXT = os.path.join(USER_DIR, "redo_next.json")  # same, written while Anki ran an older version
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


class _UserBold(HTMLParser):
    """Text you bolded in a colored sentence. The add-on's own bold (a name it already knows)
    sits right inside the text row (span.rb); furigana (span.rt) isn't part of the text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.bold, self.texts = [], 0, []

    def handle_starttag(self, tag, attrs):
        cls = (dict(attrs).get("class") or "").split()
        if tag in ("b", "strong"):
            ours = bool(self.stack) and "rb" in self.stack[-1][1]
            if not ours:
                if not self.bold:
                    self.texts.append("")
                self.bold += 1
            self.stack.append((tag, cls, not ours))
        elif tag not in ("br", "img"):
            self.stack.append((tag, cls, False))

    def handle_endtag(self, tag):
        while self.stack:
            t, _, user = self.stack.pop()
            if user:
                self.bold -= 1
            if t == tag:
                break

    def handle_data(self, data):
        if self.bold and not any("rt" in c for _, c, _ in self.stack):
            self.texts[-1] += data


def user_bold(pitch_html):
    """Texts bolded by you in the sentence-pitch field (not by the add-on)."""
    if "<b" not in pitch_html and "<strong" not in pitch_html:
        return []
    p = _UserBold()
    try:
        p.feed(pitch_html)
    except Exception:
        return []
    return [t for t in dict.fromkeys(t.strip() for t in p.texts) if t]


def bold_in_sentence(raw, texts):
    """The sentence field with these texts in bold (where they aren't already)."""
    for t in texts:
        raw = re.sub(rf"(?<!<b>){re.escape(t)}(?!</b>)", f"<b>{t}</b>", raw)
    return raw


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
            stored = get(f, spec["pitch_field"])
            set_sentence = None
            if spec.get("word_mark") != "b":  # a name you bolded in the colored sentence
                new_raw = bold_in_sentence(raw, user_bold(stored))
                set_sentence, raw = (new_raw if new_raw != raw else None), new_raw
            if spec.get("word_mark") == "b":  # the card's word is in bold (core6k), not a name
                raw = re.sub(r"(?i)<(/?)(?:b|strong)\b[^>]*>", r"<\1i>", raw)
            job = {"nid": nid, "spec": spec, "raw": raw,
                   "written": get(f, spec.get("written_field")),
                   "word": get(f, spec["word_field"]),
                   "cat": get(f, spec.get("category_field")),
                   "reading": get(f, spec.get("reading_field")),
                   "furigana": spec.get("furigana", False)}
            h = core.source_hash(raw, job["written"], job["word"], core.first_cat(job["cat"]), job["reading"])
            job["stored"] = hash(stored)  # to tell which sentences change (not the text: memory)
            if set_sentence is not None:
                job["set"] = {spec["sentence_field"]: set_sentence}
            job["stale"] = core.stored_hash(stored) != h or core.needs_fix(stored, raw) or set_sentence is not None
            jobs[nid] = job
    return jobs


def prepare(col, cfg):
    return {"notes": sentence_notes(col, cfg), "vocab": read_vocab(col, cfg)}


UNDO_NAME = "Sentence pitch"
HOLD_STATES = ("review", "overview")  # screens where Undo means "undo my last answer"
EDIT_WINDOWS = ("Browser", "EditCurrent", "AddCards")  # where Undo means "undo my edit"
HOLD_MAX = 40  # batches held back (1,000 sentences) before the worker waits for you
_held = []


def user_busy(asked=False):
    """Reviewing, or the browser or an edit window is open: then Undo should only ever undo
    what you did, so nothing is written. asked: you started this run from the menu, so it's
    written while you review too (never while an edit window could save over it)."""
    if mw.state in HOLD_STATES and not asked:
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
    for item in items:
        nid, field, html = item[:3]
        try:
            note = col.get_note(nid)
        except Exception:  # deleted meanwhile
            continue
        changed = False
        for f, v in [(field, html)] + list((item[3] if len(item) > 3 else {}).items()):
            if f in note and note[f] != v:  # (and the sentence, for a name you bolded)
                note[f] = v
                changed = True
        if changed:
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


def write_later(items, asked=False):
    """From the worker: hand one batch to the main thread."""
    mw.taskman.run_on_main(lambda: write_now(items, asked=asked))


def write_now(items, tries=0, asked=False):
    """Write one batch in a short collection step of its own, unless you're reviewing or
    editing: then it waits in _held until you're back at the deck list with the browser
    and edit windows closed (a run you started yourself only waits for those windows)."""
    if not mw.col:
        return
    if user_busy(asked):
        _held.append((items, asked))
        return

    def done(n):
        if n is None and tries < 60:
            mw.progress.single_shot(10000, lambda: write_now(items, tries + 1, asked), False)
            return
        refresh_undo_menu()
        if n and mw.state == "review":  # show the new colors on the card in front of you
            try:
                from aqt.reviewer import RefreshNeeded
                card = mw.reviewer.card
                if card and card.nid in {item[0] for item in items}:
                    mw.reviewer._refresh_needed = RefreshNeeded.NOTE_TEXT
                    mw.reviewer.refresh_if_needed()
            except Exception as e:
                log_error(e)

    QueryOp(parent=mw, op=lambda col: write_notes(col, items), success=done) \
        .failure(log_error).run_in_background()


def flush_held(*_):
    if not _held or not mw.col:
        return
    ready = [(items, asked) for items, asked in _held if not user_busy(asked)]
    if ready:
        _held[:] = [h for h in _held if h not in ready]
        for items, asked in ready:  # queued one after another; they end up as one undo step
            write_now(items, asked=asked)


def held_count():
    return sum(len(items) for items, _ in _held)


# ---------------------------------------------------------------- the slow part (no collection)

def work(prep, cfg, force=False, limit=None, progress=None, write=write_later):
    """Color what needs it. -> (notes done, notes left, stats, conflicts).
    Raises core.Unavailable if Yomitan, Suzuki-kun or the analyzer can't be reached
    (batches finished before that are kept)."""
    notes = prep["notes"]
    changed = []  # (card's word, sentence) of each sentence whose colors changed
    if not notes:
        return 0, 0, {}, [], changed
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
                return 0, 0, {}, [], changed  # Brave closed and nothing else to do: check next time
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
                items.append((job["nid"], job["spec"]["pitch_field"], html, job.get("set", {})))
                if hash(html) != job.get("stored") or job.get("set"):
                    changed.append((core.clean(job["word"]), core.clean(job["raw"])))
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
    return done, len(todo) - done, total, lookup.conflicts(), changed


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
        done, left, total, conflicts, changed = result
        # after the last batch is written (same queue), remember the collection state
        QueryOp(parent=mw, op=lambda col: col.mod, success=lambda m: _seen_mod.__setitem__(0, m)) \
            .failure(log_error).run_in_background()
        if done:
            text = changed_list(changed, done) + core.format_report(done, total, left, conflicts)
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
            finished((0, 0, {}, [], []))
            return
        write = (lambda items: write_later(items, asked=True)) if report else write_later
        QueryOp(parent=mw, op=lambda _: work(prep, cfg, force, limit, progress, write), success=finished) \
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
    try:  # notes a new version changes, listed while Anki still ran the old one: recolor them now
        later = core.load_cache(REDO_NEXT).get("notes", [])
        if later:
            now = core.load_cache(REDO).get("notes", [])
            core.save_cache(REDO, {"notes": sorted({int(x) for x in now + later})})
            os.remove(REDO_NEXT)
    except Exception as e:
        log_error(e)
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

def changed_list(changed, done, most=300):
    """The report's first part: which sentences got new colors."""
    lines = [f"Sentences with new colors: {len(changed)} of {done:,}"]
    if not changed:
        lines.append("  (all were already up to date)")
    for word, sentence in changed[:most]:
        sentence = sentence.replace("\n", " ")
        lines.append(f"  {word}: {sentence[:60] + '…' if len(sentence) > 60 else sentence}")
    if len(changed) > most:
        lines.append(f"  … and {len(changed) - most:,} more")
    waiting = held_count()
    if waiting:
        lines.append(f"Not saved yet: {waiting:,} wait until you close the browser and edit windows"
                     " (or, for the background runs, until you leave the review screen).")
    return "\n".join(lines) + "\n\n"


def show_report():
    try:
        with open(REPORT_PATH, encoding="utf-8") as f:
            showText(f.read(), title="Sentence pitch")
    except OSError:
        tooltip("No report yet")


def recolor_all():
    """Asks first: easy to hit by accident, and it draws every sentence again."""
    try:
        n = sum(len(mw.col.models.nids(m["id"])) for spec in config()["sentences"]
                if spec.get("enabled", True) and (m := mw.col.models.by_name(spec["note_type"])))
    except Exception:
        n = 0
    what = f"all {n:,} sentences" if n else "all sentences"
    if askUser(f"Recolor {what}?\n\nEvery sentence is drawn again from scratch, which takes a few "
               "minutes. Only the ones whose colors change are saved.",
               defaultno=True, title="Sentence pitch"):
        start("menu", force=True, report=True)


def setup_menu():
    menu = QMenu("Sentence pitch", mw)
    shortcut = config().get("shortcut", "Ctrl+Shift+R")  # Cmd+Shift+R on a Mac
    for label, fn, keys in (("Test: color the 20 newest sentences", lambda: start("menu", limit=20, report=True), ""),
                            ("Color new and changed sentences", lambda: start("menu", report=True), shortcut),
                            ("Recolor all sentences…", recolor_all, ""),
                            ("Show last report", show_report, "")):
        action = QAction(label, mw)
        action.triggered.connect(fn)
        if keys:
            action.setShortcut(QKeySequence(keys))
        menu.addAction(action)
    mw.form.menuTools.addMenu(menu)


gui_hooks.sync_did_finish.append(lambda: start("sync"))
gui_hooks.profile_did_open.append(on_profile_open)
gui_hooks.profile_will_close.append(on_profile_close)
gui_hooks.deck_browser_will_render_content.append(on_deck_browser)
gui_hooks.state_did_change.append(flush_held)
setup_menu()
