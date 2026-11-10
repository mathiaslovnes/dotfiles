"""Contrast the card's word with near-synonyms you already have in your deck (key c).

1. Claude (cheap model) lists near-synonyms of the word as used in the sentence.
2. Those are looked up by exact word form (or reading, for kana) in your note types.
3. You tick which ones to contrast (found ones are ticked; others listed unticked).
4. Claude (contrast model) writes one line per word into its own field
   ("contrast_field", default contrast), which the template shows at the bottom
   of the 解説 panel. Regenerating the explanation doesn't touch it.

Config: "contrast_candidate_model" (default claude-haiku-5-5),
        "contrast_model" (default claude-sonnet-5-5),
        "contrast_reading_fields" / "contrast_meaning_fields" (note type -> field)."""

from __future__ import annotations

import html
import re

from aqt import mw
from aqt.operations import QueryOp
from aqt.qt import (QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                    QScrollArea, Qt, QVBoxLayout, QWidget)
from aqt.utils import qconnect, showWarning, tooltip

from .config import CONFIG
from .logging import debug_log
from .profiles import fcfg, profile_for
from ..api_handler import generate_explanation

READING_FIELDS = {"subs2srs": "reading", "core6k": "Vocabulary-Kana"}
MEANING_FIELDS = {"subs2srs": "definition", "core6k": "Vocabulary-English"}
DEFAULT_CONTRAST_FIELD = "contrast"

CANDIDATE_PROMPT = (
    "List up to 15 Japanese words that are near-synonyms of 「{word}」 as it is used in this "
    "sentence: 「{sentence}」. Include words a learner could easily confuse with it. "
    "Also include set phrases or compounds that contain 「{word}」 if they mean nearly the same thing "
    "(e.g. 誹謗中傷 for 中傷), but not ones that only contain it (e.g. not 中傷記事). "
    "Dictionary form, one word per line in the format 語（よみ） with the reading in hiragana, "
    "e.g. 奇妙（きみょう）. No numbering, no explanations."
)
CONTRAST_PROMPT = (
    "「{word}」 is used in this sentence: 「{sentence}」\n"
    "Contrast it with these near-synonyms: {others}\n\n"
    "The reader is a learner who wants to know exactly where each word's meaning and use end and "
    "the next one's begin, and why only some of them fit this sentence.\n\n"
    "Before writing, work out what the words share and the concrete points where they differ: what "
    "each one is about, what it attaches to or describes, fixed patterns it is used in (e.g. almost "
    "always negated, almost always with one particular verb), how strong it is, and whether it is "
    "written or spoken language.\n\n"
    "Write one line per word, starting with 「{word}」 itself, then the others in the order given, "
    "in exactly this format:\n"
    "語：説明\n\n"
    "Each 説明 says, in this order:\n"
    "1. What the word itself means, precisely enough that it could not also describe the others. "
    "Never define it with another word from the list (not 際限＝限界). If it is mostly used in a "
    "fixed form, say so, but still say what the word itself means, not only the form (際限 itself "
    "means the end or limit; 際限なく means without end).\n"
    "2. Where it differs from the others: what it covers that they don't, or where it is narrower, "
    "stronger, more formal, or used in a different pattern.\n"
    "3. For the others: whether it could replace 「{word}」 here, with the reason in a few words "
    "(a different meaning, or it isn't used in that pattern). Never just 「この文には合わない」. "
    "For 「{word}」 itself, leave this out unless how it is used here isn't obvious.\n"
    "Say each point once, in as few words as it takes.\n\n"
    "Rules:\n"
    "- Japanese only, plain form (だ・である), no casual speech.\n"
    "- Write so that a Japanese native around 13 years old understands it: everyday words and "
    "common kanji. Say what differs in plain words rather than abstract terms "
    "(e.g. not 含意・範疇・限定的・婉曲的). Matter-of-fact, not childish.\n"
    "- 40 to 70 Japanese characters per word, all on one line.\n"
    "- Examples only where a set phrase or typical combination is itself the difference: then at "
    "most two short phrases in 「」. No example sentences.\n"
    "- No introduction, no readings, no headings, nothing else.\n\n"
    "Example of the level of detail, for 際限 in 「際限なくぐるぐると渦巻き続ける」 with 限度、限界:\n"
    "際限：物事の終わりや限り。ほぼ「際限がない」「際限なく」と打ち消しで使い、続いたり増えたり"
    "するものに終わりが見えない様子を言う。\n"
    "限度：これ以上はいけないと決められた量や程度の線（「限度を超える」）。終わりのなさは言えないので、"
    "この文には入らない。\n"
    "限界：力や我慢が耐えられる、ぎりぎりの所（「体力の限界」）。「限界なく」とは言わないので、"
    "この文には使えない。"
)


def _clean(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    s = re.sub(r"\[[^\]]*\]", "", s)          # furigana brackets 漢字[かんじ]
    return re.sub(r"\s+", "", s)


def _is_kana(s: str) -> bool:
    return bool(s) and all("぀" <= c <= "ヿ" or c == "ー" for c in s)


def _profiles() -> list:
    names = [CONFIG.get("note_type")]
    names += [p.get("note_type") for p in CONFIG.get("extra_note_types") or [] if isinstance(p, dict)]
    return [n for n in names if n]


def _build_index():
    """word form -> entries, reading -> entries; entry = (nid, word, meaning snippet, reading)."""
    by_word, by_reading = {}, {}
    reading_fields = CONFIG.get("contrast_reading_fields") or READING_FIELDS
    meaning_fields = CONFIG.get("contrast_meaning_fields") or MEANING_FIELDS
    for name in _profiles():
        model = mw.col.models.by_name(name)
        if not model:
            continue
        fields = [f["name"] for f in model["flds"]]
        prof = profile_for(name) or CONFIG
        wf = prof.get("word_field") or CONFIG.get("word_field")
        if wf not in fields:
            continue
        wi = fields.index(wf)
        ri = fields.index(reading_fields[name]) if reading_fields.get(name) in fields else None
        mi = fields.index(meaning_fields[name]) if meaning_fields.get(name) in fields else None
        for nid, flds in mw.col.db.all("select id, flds from notes where mid = ?", model["id"]):
            vals = flds.split("\x1f")
            word = _clean(vals[wi]) if wi < len(vals) else ""
            if not word:
                continue
            meaning = html.unescape(re.sub(r"<[^>]+>", " ", vals[mi])) if mi is not None and mi < len(vals) else ""
            reading = _clean(vals[ri]) if ri is not None and ri < len(vals) else ""
            entry = (nid, word, re.sub(r"\s+", " ", meaning).strip()[:70], reading)
            by_word.setdefault(word, []).append(entry)
            if reading:
                by_reading.setdefault(reading, []).append(entry)
    return by_word, by_reading


def _parse_candidates(text: str) -> list:
    """Lines like 奇妙（きみょう） -> [(word, reading)]; reading may be ""."""
    out, seen = [], set()
    for line in text.splitlines():
        line = re.sub(r"^[\s\-・*•\d.)）]+", "", line).strip()
        m = re.match(r"^([^\s(（:：、,]+)\s*[(（]\s*([ぁ-んァ-ンー]+)\s*[)）]", line)
        word, reading = (m.group(1), m.group(2)) if m else (re.split(r"[\s(（:：、,]", line)[0] if line else "", "")
        if word and word not in seen:
            seen.add(word)
            out.append((word, reading))
    return out


def _target_reading(note) -> str:
    fields = CONFIG.get("contrast_reading_fields") or READING_FIELDS
    rf = fields.get(note.note_type()["name"])
    return _clean(note[rf]) if rf and rf in note else ""


def _label(word: str, reading: str) -> str:
    return f"{word}（{reading}）" if reading and reading != word else word


def _hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def _ruby(word: str, reading: str) -> str:
    """Furigana over the kanji only: 取り除く + とりのぞく -> 取(と)り除(のぞ)く. A span with the reading
    in data-r (drawn by the card's CSS), not <ruby>: iPhone misplaces an absolutely positioned <rt>."""
    w = html.escape(word)
    if not reading or reading == word or _is_kana(word):
        return w
    parts = re.findall(r"[ぁ-ゟァ-ヿー]+|[^ぁ-ゟァ-ヿー]+", word)
    pattern = "".join(f"({re.escape(_hira(p))})" if _is_kana(p) else "(.+?)" for p in parts)
    m = re.fullmatch(pattern, _hira(reading))
    if not m:
        return f'<span class="fr" data-r="{html.escape(reading)}">{w}</span>'
    return "".join(html.escape(p) if _is_kana(p) else
                   f'<span class="fr" data-r="{html.escape(reading[m.start(i + 1):m.end(i + 1)])}">{html.escape(p)}</span>'
                   for i, p in enumerate(parts))


def _existing(note) -> list:
    """[(word, reading)] already in the note's contrast field, the card's own word excluded.
    The reading comes back from the furigana spans: <span data-r="と">取</span>り -> とり."""
    cf = fcfg(note, "contrast_field") or DEFAULT_CONTRAST_FIELD
    if cf not in note:
        return []
    out = []
    for line in _lines(note[cf]):
        m = re.search(r"<b>(.*?)</b>", line, re.S)
        if not m:
            continue
        word, reading, ruby = "", "", False
        for span_r, span_text, text in re.findall(r'<span class="fr" data-r="([^"]*)">(.*?)</span>|([^<]+)', m.group(1)):
            if span_text:
                word, reading, ruby = word + html.unescape(span_text), reading + html.unescape(span_r), True
            elif text:
                word, reading = word + html.unescape(text), reading + html.unescape(text)
        word = _clean(word)
        if word and word not in [w for w, _ in out]:
            out.append((word, reading if ruby else ""))
    return out


class _AddEdit(QLineEdit):
    """Enter adds the typed word instead of pressing Generate."""

    def __init__(self, on_enter):
        super().__init__()
        self._on_enter = on_enter

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_enter()
            e.accept()
            return
        super().keyPressEvent(e)


class PickDialog(QDialog):
    """Tick the words to contrast with. Found-in-deck ones start ticked.
    Words the list missed can be typed in below it."""

    def __init__(self, word, known, others, lookup=None, parent=None, sentence="", step="", current=()):
        super().__init__(parent or mw)
        font = self.font()
        font.setPointSizeF(font.pointSizeF() * 1.4)    # kanji readable without zooming in
        self.setFont(font)
        small = self.font()
        small.setPointSizeF(font.pointSizeF() * 0.8)
        self.setWindowTitle(f"Contrast 「{word}」 with…{step}")
        self.word, self.lookup, self.readings = word, lookup, {}
        self.boxes, self.skipped = [], False
        outer = QVBoxLayout(self)
        if sentence:                              # from the Browser: the card isn't on screen
            shown = html.escape(sentence).replace("\n", "<br>")
            shown = shown.replace(html.escape(word), f"<b>{html.escape(word)}</b>")
            label = QLabel(shown)
            label.setWordWrap(True)
            label.setStyleSheet("color: gray; margin-bottom: 6px;")
            label.setFont(font)
            outer.addWidget(label)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        if current:                               # regenerating: keep what the contrast has now
            heading = QLabel("<b>In the contrast now</b> (untick to drop)")
            heading.setWordWrap(True)
            lay.addWidget(heading)
            for w, reading in current:
                box = QCheckBox(_label(w, reading or (lookup(w) if lookup else "")))
                box.setChecked(True)
                box.setProperty("word", w)
                self.boxes.append(box)
                lay.addWidget(box)
        if known:
            heading = QLabel("<b>In your deck</b> (untick the ones you already tell apart)")
            heading.setWordWrap(True)
            lay.addWidget(heading)
            for w, reading, meaning in known:
                box = QCheckBox(_label(w, reading))
                box.setChecked(True)
                box.setProperty("word", w)
                self.boxes.append(box)
                row = QHBoxLayout()
                row.addWidget(box)
                if meaning:                       # beside the word, wrapped, so nothing scrolls sideways
                    gloss = QLabel(meaning if len(meaning) <= 80 else meaning[:80] + "…")
                    gloss.setWordWrap(True)
                    gloss.setStyleSheet("color: gray; margin-left: 10px;")
                    gloss.setFont(small)
                    row.addWidget(gloss, 1)
                else:
                    row.addStretch()
                lay.addLayout(row)
        if others:
            lay.addWidget(QLabel("<b>Not in your deck</b>"))
            for w, reading in others:
                box = QCheckBox(_label(w, reading))
                box.setProperty("word", w)
                self.boxes.append(box)
                lay.addWidget(box)
        self.added = QVBoxLayout()
        lay.addLayout(self.added)
        lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        add_row = QHBoxLayout()
        self.add_edit = _AddEdit(self._add)
        self.add_edit.setPlaceholderText("Add a word the list missed")
        add_btn = QPushButton("Add")
        add_btn.setAutoDefault(False)
        qconnect(add_btn.clicked, self._add)
        add_row.addWidget(self.add_edit)
        add_row.addWidget(add_btn)
        outer.addLayout(add_row)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel, ok = QPushButton("Cancel" if not step else "Stop"), QPushButton("Generate")
        ok.setDefault(True)
        qconnect(cancel.clicked, self.reject)
        qconnect(ok.clicked, self.accept)
        buttons.addWidget(cancel)
        if step:                                  # one of several notes: Skip goes on to the next
            skip = QPushButton("Skip")
            skip.setAutoDefault(False)
            qconnect(skip.clicked, self._skip)
            buttons.addWidget(skip)
        buttons.addWidget(ok)
        outer.addLayout(buttons)
        self.resize(660, 720)

    def _skip(self) -> None:
        self.skipped = True
        self.reject()

    def _add(self) -> None:
        w = _clean(self.add_edit.text())
        if not w:
            return
        self.add_edit.clear()
        if w == self.word:
            return
        for b in self.boxes:
            if b.property("word") == w:
                b.setChecked(True)
                return
        reading = self.lookup(w) if self.lookup else ""
        if not self.readings:
            self.added.addWidget(QLabel("<b>Added</b>"))
        self.readings[w] = reading
        box = QCheckBox(_label(w, reading))
        box.setChecked(True)
        box.setProperty("word", w)
        self.boxes.append(box)
        self.added.addWidget(box)

    def chosen(self) -> list:
        return [b.property("word") for b in self.boxes if b.isChecked()]


def start_contrast() -> None:
    """Reviewer: c / Shift+C."""
    card = mw.reviewer.card if mw.state == "review" else None
    if card:
        _contrast(card.note())


def contrast_notes(nids, parent=None) -> None:
    """Browser: the picker opens for one note after another. Each contrast is written in
    the background while you pick the next; Skip goes on, Stop ends the series."""
    queue, total = list(nids), len(nids)

    def next_one() -> None:
        while queue:
            nid = queue.pop(0)
            try:
                note = mw.col.get_note(nid)
            except Exception:
                continue
            step = f"  ({total - len(queue)}/{total})" if total > 1 else ""
            _contrast(note, parent=parent, step=step, on_next=next_one, from_browser=True)
            return

    if not CONFIG.get("api_key"):
        tooltip("No Claude API key set.", parent=parent)
        return
    next_one()


def _contrast(note, parent=None, step="", on_next=None, from_browser=False) -> None:
    on_next = on_next or (lambda: None)
    if profile_for(note.note_type()["name"]) is None:
        tooltip("This note type isn't set up in AI Language Explainer.", parent=parent)
        on_next()
        return
    if not CONFIG.get("api_key"):
        tooltip("No Claude API key set.", parent=parent)
        return
    wf, sf = fcfg(note, "word_field"), fcfg(note, "sentence_field")
    word = _clean(note[wf]) if wf in note else ""
    sentence = re.sub(r"<[^>]+>", "", re.sub(r"(?i)<br\s*/?>", "\n", note[sf])) if sf in note else ""
    if not word:
        tooltip("No word on this card.", parent=parent)
        on_next()
        return
    nid = note.id
    word_reading = _target_reading(note)
    model = CONFIG.get("contrast_candidate_model") or "claude-haiku-5-5"

    def ask(_col):
        prompt = CANDIDATE_PROMPT.format(word=word, sentence=sentence)
        return _parse_candidates(generate_explanation(CONFIG["api_key"], prompt, model))

    current = [(w, r) for w, r in _existing(note) if w != word]

    def got(candidates):
        by_word, by_reading = _build_index()
        known, others, seen = [], [], {word} | {w for w, _ in current}
        readings = {word: word_reading}
        for w, r in current:                     # an older contrast has no furigana: take your card's
            hits = [h for h in by_word.get(w, []) if h[0] != nid]
            readings[w] = r or (hits[0][3] if hits else "")
        for cand, cand_reading in candidates:
            key = _clean(cand)
            if not key or key in seen:
                continue
            if key.endswith("な") and key not in by_word and key[:-1] in by_word:
                key = key[:-1]                   # 変な -> 変
            hits = by_word.get(key) or (by_reading.get(key) if _is_kana(key) else None)
            hits = [h for h in (hits or []) if h[0] != nid]
            if hits:
                w = hits[0][1]
                if w not in seen:
                    readings[w] = hits[0][3] or cand_reading     # your card's reading first
                    known.append((w, readings[w], hits[0][2]))
                    seen.add(w)
            else:
                readings[key] = cand_reading
                others.append((key, cand_reading))
                seen.add(key)
        def lookup(w):                           # reading from your card, if you have the word
            hits = [h for h in by_word.get(w, []) if h[0] != nid]
            return hits[0][3] if hits else ""

        dlg = PickDialog(word, known, others[:6], lookup, parent=parent,
                         sentence=sentence if from_browser else "", step=step, current=current)
        if dlg.exec():
            if dlg.chosen():
                for w, r in dlg.readings.items():
                    readings.setdefault(w, r)
                _write(nid, word, sentence, dlg.chosen(), readings, parent, from_browser)
            on_next()
        elif dlg.skipped:
            on_next()

    def failed(e) -> None:
        showWarning(f"Contrast failed for {word}: {e}", parent=parent)
        on_next()

    (QueryOp(parent=parent or mw, op=ask, success=got)
     .failure(failed)
     .without_collection()                       # only calls Claude; doesn't wait for other ops
     .with_progress(f"Finding near-synonyms of {word}…{step}")
     .run_in_background())


def _write(nid, word, sentence, others, readings, parent=None, from_browser=False) -> None:
    """In the Browser it runs without a progress window, so the next picker can open."""
    model = CONFIG.get("contrast_model") or "claude-sonnet-5-5"

    def ask(_col):
        prompt = CONTRAST_PROMPT.format(word=word, sentence=sentence, others="、".join(others))
        return generate_explanation(CONFIG["api_key"], prompt, model)

    def got(text):
        lines = []
        for line in text.splitlines():
            m = re.match(r"^\s*[「『]?([^：:」』]+)[」』]?\s*[：:]\s*(.+)$", line)
            if m:
                head = m.group(1).strip()
                lines.append(f"<b>{_ruby(head, readings.get(head, ''))}</b>：{html.escape(m.group(2).strip())}")
        if not lines:
            showWarning(f"Couldn't read the contrast for {word}:\n{text}", parent=parent)
            return
        try:
            note = mw.col.get_note(nid)
        except Exception:
            return
        cf = fcfg(note, "contrast_field") or DEFAULT_CONTRAST_FIELD
        if cf not in note:
            tooltip(f"No field {cf} on this note type. Add it to use contrasts.", parent=parent)
            return
        note[cf] = "".join(f'<div class="llm-cl">{line}</div>' for line in lines)  # replaces an earlier one
        mw.col.update_note(note)
        if from_browser:
            tooltip(f"Contrast added: {word}", parent=parent)
            notify_note_changed()
            return
        tooltip("Contrast added")
        if mw.state == "review" and mw.reviewer.card and mw.reviewer.card.nid == nid:
            from .panel import redraw_and_reveal
            redraw_and_reveal("con")

    op = (QueryOp(parent=parent or mw, op=ask, success=got)
          .failure(lambda e: showWarning(f"Contrast failed for {word}: {e}", parent=parent))
          .without_collection())
    if not from_browser:
        op = op.with_progress(f"Contrasting {word}…")
    op.run_in_background()


def notify_note_changed() -> None:
    """Tell the Browser (and the reviewer) that note text changed, as Anki's own edits do.
    Otherwise the Browser's editor keeps the old note and a later edit there writes the old
    field back."""
    from anki.collection import OpChanges
    from aqt import gui_hooks
    gui_hooks.operation_did_execute(OpChanges(note_text=True), None)


def _lines(value: str) -> list:
    found = re.findall(r'<div class="llm-cl">(.*?)</div>', value or "", re.S)
    if found:
        return found
    return [part for part in re.split(r"<br\s*/?>", value or "") if part.strip()]   # older format


def remove_line(nid: int, index: int) -> None:
    try:
        note = mw.col.get_note(nid)
    except Exception:
        return
    cf = fcfg(note, "contrast_field") or DEFAULT_CONTRAST_FIELD
    if cf not in note:
        return
    lines = _lines(note[cf])
    if 0 <= index < len(lines):
        del lines[index]
        note[cf] = "".join(f'<div class="llm-cl">{line}</div>' for line in lines)
        mw.col.update_note(note)
        card = mw.reviewer.card if mw.state == "review" else None
        if card and card.nid == nid:
            card.note(reload=True)   # so c / g see the edited field without a redraw


def on_js_message(handled, message, context):
    """× on a contrast line sends alx_cdel:<note id>:<line index>."""
    if isinstance(message, str) and message.startswith("alx_cdel:"):
        try:
            _, nid, index = message.split(":")
            remove_line(int(nid), int(index))
        except Exception as e:
            debug_log(f"contrast: remove failed: {e}")
        return (True, None)
    return handled


_REMOVE_JS = """<script>
(function () {
  if (typeof pycmd !== 'function') return;
  var box = document.querySelector('#llmDefinition .llm-contrast');
  if (!box) return;
  box.querySelectorAll('.llm-cl').forEach(function (line) {
    if (line.querySelector('.llm-cl-x')) return;
    var x = document.createElement('span');
    x.className = 'llm-cl-x';
    x.textContent = '×';
    x.title = 'Remove this word from the contrast';
    x.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      var index = Array.prototype.indexOf.call(box.querySelectorAll('.llm-cl'), line);
      pycmd('alx_cdel:%d:' + index);
      line.remove();
      if (!box.querySelector('.llm-cl')) {
        var d = document.getElementById('llmDefinition');
        box.remove();
        if (d) {
          d.classList.remove('has-con', 'hide-con');
          if (d.classList.contains('hide-exp')) d.open = false;
        }
      }
    });
    line.insertBefore(x, line.firstChild);
  });
})();
</script>"""


def add_remove_buttons(text: str, card, kind: str) -> str:
    """Desktop review, answer side: a × in front of every contrast line."""
    if kind == "reviewAnswer" and 'class="llm-cl"' in text:
        return text + _REMOVE_JS % card.nid
    return text


__all__ = ["start_contrast", "contrast_notes", "notify_note_changed", "on_js_message", "add_remove_buttons"]
