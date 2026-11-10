"""Clip cutter: cut a card's sentence audio down to part of the sentence.

Editor button ✂ (Cmd+Control+X: "Ctrl+Meta+X" in Qt terms) on subs2srs notes opens a window with the sentence:
- select text and press "Fit to selection": the audio is cut to where that text is spoken
  (speech recognition finds it; the first time a clip is opened it takes a few seconds)
- or drag the start and end sliders yourself; P plays the cut, Ctrl+Enter saves
- "Also cut the sentence" trims the sentence field to the selected text
The original audio file stays in your media folder, with a copy in user_files/originals (Check Media's
"Delete Unused" would remove the original once no card points at it), and "Restore original" puts it back.
Tools > Clip cutter > "Transcribe in the background" pre-processes cards so the window opens instantly.
"""
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading

from aqt import gui_hooks, mw
from aqt.operations.note import update_note
from aqt.qt import (QAction, QApplication, QCheckBox, QColor, QDialog, QDialogButtonBox, QDoubleSpinBox, QFont,
                    QHBoxLayout, QKeySequence, QLabel, QMenu, QPainter, QPalette, QPen, QPlainTextEdit, QPointF,
                    QPushButton, QRectF, QShortcut, QSizePolicy, QSplitter, Qt, QTextCursor, QVBoxLayout, QWidget,
                    pyqtSignal)
from aqt.sound import av_player, play_clicked_audio
from aqt.theme import theme_manager
from aqt.utils import showWarning, tooltip
from aqt.webview import AnkiWebView

HERE = os.path.dirname(os.path.abspath(__file__))
UF = os.path.join(HERE, "user_files")
ORIG = os.path.join(UF, "originals.json")
KEEP = os.path.join(UF, "originals")
os.makedirs(os.path.join(UF, "asr"), exist_ok=True)


def cfg():
    return mw.addonManager.getConfig(__name__)


# ---------------------------------------------------------------- speech recognition process

class Worker:
    def __init__(self):
        self.p = None
        self.lock = threading.Lock()

    def ask(self, req):
        with self.lock:
            if self.p is None or self.p.poll() is not None:
                c = cfg()
                self.p = subprocess.Popen(
                    [os.path.expanduser(c["python"]), os.path.join(HERE, "worker.py"), os.path.join(UF, "asr"),
                     c["model"], c["ffmpeg"]],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    text=True, encoding="utf-8", bufsize=1)
            self.p.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            self.p.stdin.flush()
            line = self.p.stdout.readline()
            if not line:
                self.p = None
                raise RuntimeError("the speech recognition process stopped")
            r = json.loads(line)
            if "error" in r:
                raise RuntimeError(r["error"])
            return r

    def close(self):
        if self.p and self.p.poll() is None:
            try:
                self.p.stdin.close()
                self.p.terminate()
            except Exception:
                pass
        self.p = None


WORKER = Worker()


# ---------------------------------------------------------------- helpers

SEG = re.compile(r"<[^>]+>|&[#\w]+;|.", re.S)
FMT = re.compile(r"<(/?)(i|b|u|em|strong|span|font|ruby|rt)\b[^>]*>", re.I)


def html_map(s):
    """displayed text of a field (<br> = new line) and, per character, its (start, end) in the HTML"""
    out, spans = [], []
    for m in SEG.finditer(s or ""):
        t = m.group(0)
        if t.startswith("<"):
            if re.match(r"<br\b", t, re.I) or re.match(r"</(div|p)>", t, re.I):
                out.append("\n")
                spans.append((m.start(), m.end()))
            continue
        if t.startswith("&") and len(t) > 1:
            t = html.unescape(t)
        for ch in t:
            out.append(" " if ch in "\xa0\n\r\t" else ch)  # line breaks in the HTML source don't show
            spans.append((m.start(), m.end()))
    return "".join(out), spans


def is_jp(ch):
    return bool(ch) and ("　" <= ch <= "ヿ" or "一" <= ch <= "鿿" or "＀" <= ch <= "￯")


def lines_at_spaces(t):
    """Each subtitle line on its own line: a space next to Japanese text becomes a line break
    (one character for one, so positions still match the field)."""
    chars = list(t)
    for k, ch in enumerate(chars):
        if ch in " 　":
            prev = next((c for c in reversed(t[:k]) if c not in " 　\n‎"), "")
            nxt = next((c for c in t[k + 1:] if c not in " 　\n‎"), "")
            if is_jp(prev) or is_jp(nxt):
                chars[k] = "\n"
    # one line break between lines: a space next to a <br> (" 脳の寿命は"), a second <br> and
    # breaks at the start or end become an invisible zero-width space (still one character)
    out = []
    for ch in chars:
        last = next((c for c in reversed(out) if c != "​"), "")
        out.append("​" if ch == "\n" and last in ("", "\n") else ch)
    for k in range(len(out) - 1, -1, -1):
        if out[k] not in ("\n", "​"):
            break
        out[k] = "​"
    return "".join(out)


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


class RangeSlider(QWidget):
    """One track, two handles: start on the left, end on the right (hundredths of a second).
    Ticks under the track show where speech recognition heard words begin."""
    changed = pyqtSignal(int, int)
    R = 10

    def __init__(self, maximum, parent=None):
        super().__init__(parent)
        self.max = max(1, maximum)
        self.lo, self.hi = 0, self.max
        self.marks = []
        self.drag = None
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _x(self, v):
        return self.R + (self.width() - 2 * self.R) * v / self.max

    def _v(self, x):
        w = max(1, self.width() - 2 * self.R)
        return int(round(min(max((x - self.R) / w, 0.0), 1.0) * self.max))

    def set_values(self, lo, hi):
        lo, hi = max(0, min(lo, self.max)), max(0, min(hi, self.max))
        if (lo, hi) != (self.lo, self.hi):
            self.lo, self.hi = lo, hi
            self.update()
            self.changed.emit(lo, hi)

    def set_marks(self, marks):
        self.marks = marks
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() / 2 - 3
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(128, 128, 128, 90))
        p.drawRoundedRect(QRectF(self.R, y - 3, self.width() - 2 * self.R, 6), 3, 3)
        p.setBrush(self.palette().color(QPalette.ColorRole.Highlight))
        p.drawRoundedRect(QRectF(self._x(self.lo), y - 3, self._x(self.hi) - self._x(self.lo), 6), 3, 3)
        p.setPen(QPen(QColor(150, 150, 150, 160), 1))
        for m in self.marks:
            x = self._x(m)
            p.drawLine(QPointF(x, y + 9), QPointF(x, y + 15))
        p.setPen(QPen(QColor(0, 0, 0, 70), 1))
        p.setBrush(QColor(245, 245, 245))
        for v in (self.lo, self.hi):
            p.drawEllipse(QPointF(self._x(v), y), self.R, self.R)

    def mousePressEvent(self, e):
        x = e.position().x()
        dlo, dhi = abs(x - self._x(self.lo)), abs(x - self._x(self.hi))
        self.drag = "lo" if dlo < dhi or (dlo == dhi and x < self._x(self.lo)) else "hi"
        self.mouseMoveEvent(e)

    def mouseMoveEvent(self, e):
        if not self.drag:
            return
        v = self._v(e.position().x())
        if self.drag == "lo":
            self.set_values(min(v, self.hi), self.hi)
        else:
            self.set_values(self.lo, max(v, self.lo))

    def mouseReleaseEvent(self, e):
        self.drag = None


def cut_html(s, a, b):
    """the part of field HTML s shown as characters a..b, with formatting tags kept balanced"""
    text, spans = html_map(s)
    while a < b and text[a] in " \n　‎‪‬​":
        a += 1
    while b > a and text[b - 1] in " \n　‎‪‬​":
        b -= 1
    if a >= b:
        return s
    A, B = spans[a][0], spans[b - 1][1]
    stack = []
    for m in FMT.finditer(s[:A]):
        name = m.group(2).lower()
        if m.group(1):
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == name:
                    del stack[k]
                    break
        else:
            stack.append((name, m.group(0)))
    seg = s[A:B]
    still = [n for n, _ in stack]
    for m in FMT.finditer(seg):
        name = m.group(2).lower()
        if m.group(1):
            if name in still:
                still.reverse(); still.remove(name); still.reverse()
        else:
            still.append(name)
    return "".join(t for _, t in stack) + seg + "".join(f"</{n}>" for n in reversed(still))


def originals():
    try:
        with open(ORIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_originals(d):
    with open(ORIG, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def keep_copy(name):
    """A copy of an original clip in user_files/originals: once a card points at the cut,
    Check Media counts the original as unused, and "Delete Unused" would remove it."""
    if not name:
        return
    src, dst = os.path.join(mw.col.media.dir(), name), os.path.join(KEEP, name)
    if os.path.exists(src) and not os.path.exists(dst):
        os.makedirs(KEEP, exist_ok=True)
        shutil.copy2(src, dst)


def media_back(name):
    """Put an original clip back in the media folder from the copy if it went missing."""
    if not name:
        return
    src, dst = os.path.join(KEEP, name), os.path.join(mw.col.media.dir(), name)
    if not os.path.exists(dst) and os.path.exists(src):
        shutil.copy2(src, dst)


def copy_all_originals():
    for o in originals().values():
        try:
            keep_copy(o["audio"])
        except Exception:
            pass


def duration(path):
    r = subprocess.run([cfg()["ffprobe"], "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def make_cut(src, t0, t1, dest):
    fade_out = max(0.0, t1 - t0 - 0.06)
    subprocess.run([cfg()["ffmpeg"], "-y", "-loglevel", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", src,
                    "-af", f"afade=t=in:d=0.04,afade=t=out:st={fade_out:.3f}:d=0.06",
                    "-c:a", "libmp3lame", "-q:a", "2", dest], check=True)


# ---------------------------------------------------------------- the window

TAG_CUT, TAG_KEPT = "clip-cut::edited", "clip-cut::kept"  # reviewed and changed / reviewed, left as is
PROPOSALS = os.path.join(UF, "proposals.json")


def proposals():
    """{note id: {"a", "b", "text", "full"}}: cuts proposed ahead of time (a..b in the
    sentence as the window shows it, "full")."""
    try:
        with open(PROPOSALS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def tag_cut_notes():
    """Cards cut before cuts were tagged get clip-cut::edited (once: after that, saving tags,
    and removing the tag by hand puts a card back in the queue)."""
    marker = os.path.join(UF, ".cut_tags_done")
    if os.path.exists(marker):
        return
    open(marker, "w").close()
    try:
        want = {int(k) for k in originals()}
        have = set(mw.col.find_notes(f"tag:{TAG_CUT}"))
        missing = [nid for nid in want - have if mw.col.db.scalar("select 1 from notes where id = ?", nid)]
        if missing:
            mw.col.tags.bulk_add(missing, TAG_CUT)
    except Exception:
        pass


class Cutter(QDialog):
    def __init__(self, editor, note, src_name, orig, queue=None):
        super().__init__(editor.widget if editor else mw)
        self.editor, self.note, self.orig, self.queue = editor, note, orig, queue
        self.go_next = False
        self.closed = False  # set when the window closes: late speech-recognition results are ignored
        # destroyed when closed: a hidden window kept its card preview's graphics memory (GBs after
        # a long queue)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        c = cfg()
        self.c = c
        self.src_name = src_name
        self.text_only = not src_name  # a card without sentence audio (book sentences): text only
        self.src = os.path.join(mw.col.media.dir(), src_name) if src_name else None
        self.dur = (duration(self.src) or 1.0) if self.src else 1.0
        # already cut: work from the original sentence (the audio is the original too), with
        # the current cut selected, so a new cut can take more or less of it
        self.html = orig["sentence"] if orig and orig.get("sentence") else note[c["sentence_field"]]
        self.current = note[c["sentence_field"]]
        self.text = lines_at_spaces(html_map(self.html)[0])
        self.words = None
        self.sel = None
        self.tmp = os.path.join(tempfile.gettempdir(), "clip_cutter_preview.mp3")
        self.setWindowTitle("Clip cutter")
        outer = QVBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(split)
        left = QWidget()
        v = QVBoxLayout(left)
        v.setContentsMargins(0, 0, 8, 0)
        split.addWidget(left)
        self.card, self.web = None, None
        screen = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        w, h = int(screen.width() * 0.92), int(screen.height() * 0.9)
        if note.id and note.cards():
            self.card = note.cards()[0]
            self.web = AnkiWebView(self, title="clip cutter preview")
            self.web.stdHtml(mw.reviewer.revHtml(), css=["css/reviewer.css"],
                             js=["js/mathjax.js", "js/vendor/mathjax/tex-chtml-full.js", "js/reviewer.js"],
                             context=self)
            self.web.set_bridge_command(self._on_bridge, self)
            split.addWidget(self.web)
            self._show_card()
            split.setSizes([w // 2, w - w // 2])
        else:
            w = w // 2
        self.resize(w, h)
        self.move(screen.center().x() - w // 2, screen.center().y() - h // 2)

        self.view = QPlainTextEdit(self.text)
        self.view.setReadOnly(True)
        f = QFont(); f.setPointSize(c.get("font_size", 26)); self.view.setFont(f)
        self.hint = QLabel("Select the part of the sentence you want to keep, then Fit to selection:")
        v.addWidget(self.hint)
        v.addWidget(self.view, 1)

        row = QHBoxLayout()
        self.fit_btn = QPushButton("Fit to selection")
        self.fit_btn.clicked.connect(self.fit)
        self.status = QLabel("Listening to the clip…")
        row.addWidget(self.fit_btn); row.addWidget(self.status, 1)
        v.addLayout(row)

        self._range_row(v)
        self.set_times(0.0, self.dur)

        row = QHBoxLayout()
        b1 = QPushButton("▶ Cut  (P)"); b1.clicked.connect(self.play_cut)
        b2 = QPushButton("▶ Whole clip"); b2.clicked.connect(lambda: self.play(self.src))
        row.addWidget(b1); row.addWidget(b2); row.addStretch(1)
        self.play_btns = [b1, b2]
        if orig:
            b3 = QPushButton("Restore original"); b3.clicked.connect(self.restore); row.addWidget(b3)
        v.addLayout(row)

        self.cut_text = QCheckBox("Also cut the sentence to the selected text")
        self.cut_text.setEnabled(False)
        v.addWidget(self.cut_text)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.save)
        bb.rejected.connect(self.reject)
        if queue:
            self.setWindowTitle(f"Clip cutter: {queue['i'] + 1} of {queue['total']}  ({plain(note[c.get('word_field', 'word')])})"
                                + ("  (already cut)" if orig else ""))
            bb.button(QDialogButtonBox.StandardButton.Save).setText("Save && next")
            bb.button(QDialogButtonBox.StandardButton.Cancel).setText("Stop")
            keep = bb.addButton("Keep as is && next", QDialogButtonBox.ButtonRole.ActionRole)
            keep.clicked.connect(self.keep_as_is)
            back = bb.addButton("◀ Back", QDialogButtonBox.ButtonRole.ActionRole)
            back.clicked.connect(self.back)
            back.setEnabled(queue["i"] > 0)
        v.addWidget(bb)
        QShortcut(QKeySequence("P"), self, activated=self.play_cut)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.save)

        prev = re.search(r"_cut(\d+)-(\d+)\.mp3$", note[c["audio_field"]].strip("[]").replace("sound:", ""))
        if orig and prev:
            self.set_times(int(prev.group(1)) / 1000, int(prev.group(2)) / 1000)
        if orig:  # the part kept now, selected in the original sentence
            cur = lines_at_spaces(html_map(self.current)[0]).strip(" \n　​‎")
            a = self.text.find(cur) if cur else -1
            if a >= 0 and cur != self.text.strip(" \n　​‎"):
                tc = self.view.textCursor()
                tc.setPosition(a); tc.setPosition(a + len(cur), QTextCursor.MoveMode.KeepAnchor)
                self.view.setTextCursor(tc)
                self.sel = (a, a + len(cur))
                self.cut_text.setEnabled(True)
                self.cut_text.setChecked(True)
        if self.text_only:
            self._text_only_setup(v)
            return
        self.fit_btn.setEnabled(False)
        mw.taskman.run_in_background(lambda: WORKER.ask({"cmd": "asr", "path": self.src}), self._heard)

    def _text_only_setup(self, v):
        """No audio: only the sentence is cut. The audio controls are hidden; the proposed
        part (or the current cut) is selected, and Save keeps whatever is selected."""
        for w in [self.fit_btn, self.range, self.s_spin, self.e_spin, self.cut_text] + self.play_btns:
            w.hide()
        self.hint.setText("No audio on this card. Select the part of the sentence you want to keep:")
        if self.orig:
            self.status.setText("Already cut: the current cut is selected. Select other text, or Restore original.")
            return
        p = proposals().get(str(self.note.id)) if self.note.id else None
        a = b = -1
        if p:
            a, b = (p["a"], p["b"]) if self.text == p.get("full") else (self.text.find(p["text"]), -1)
            if a >= 0 and b < 0:
                b = a + len(p["text"])
        if a >= 0:
            tc = self.view.textCursor()
            tc.setPosition(a); tc.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
            self.view.setTextCursor(tc)
            self.status.setText("Proposed cut selected.")
        else:
            self.status.setText("Select the part to keep.")

    # the card's back side, as in a review (word, definition, picture), without autoplay
    def _show_card(self):
        c = self.card
        c.question(reload=True)
        txt = re.sub(r"\[\[type:[^]]+\]\]", "", c.answer())
        txt = mw.prepare_card_text_for_display(txt)
        txt = gui_hooks.card_will_show(txt, c, "previewAnswer")
        self.web.eval(f"_showAnswer({json.dumps(txt)}, '{theme_manager.body_classes_for_card_ord(c.ord)}');")

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_centered", False):
            self._centered = True
            mw.progress.single_shot(0, self._center, False)

    def _center(self):
        """Centre the whole window, title bar included, on the screen it's on, shrinking it
        first if it doesn't fit (resize() sets the size without the title bar)."""
        scr = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        fg = self.frameGeometry()
        extra_w, extra_h = fg.width() - self.width(), fg.height() - self.height()
        if fg.width() > scr.width() or fg.height() > scr.height():
            self.resize(min(self.width(), scr.width() - extra_w), min(self.height(), scr.height() - extra_h))
            fg = self.frameGeometry()
        fg.moveCenter(scr.center())
        self.move(fg.topLeft())

    def _on_bridge(self, cmd):
        if cmd.startswith("play:") and self.card:
            play_clicked_audio(cmd, self.card)

    def done(self, r):
        av_player.stop_and_clear_queue()
        if self.web:
            self.web.cleanup()
            self.web = None
        self.closed = True
        super().done(r)
        self.deleteLater()
        if self.queue and self.go_next:
            q, step = self.queue, {True: 1, "back": -1, "same": 0}[self.go_next]
            mw.progress.single_shot(200, lambda: open_next(q, step))

    def back(self):
        """Queue: close this card unchanged and open the one before it."""
        self.go_next = "back"
        self.reject()

    def _range_row(self, v):
        """start box | one slider with a start and an end handle | end box"""
        row = QHBoxLayout()
        boxes = []
        for _ in range(2):
            sp = QDoubleSpinBox()
            sp.setRange(0, self.dur); sp.setDecimals(2); sp.setSingleStep(0.05); sp.setSuffix(" s")
            boxes.append(sp)
        self.s_spin, self.e_spin = boxes
        self.range = RangeSlider(int(round(self.dur * 100)))
        row.addWidget(self.s_spin); row.addWidget(self.range, 1); row.addWidget(self.e_spin)
        v.addLayout(row)

        def from_slider(lo, hi):
            for sp, x in ((self.s_spin, lo), (self.e_spin, hi)):
                if abs(sp.value() - x / 100) > 0.004:
                    sp.setValue(x / 100)
        self.range.changed.connect(from_slider)
        self.s_spin.valueChanged.connect(
            lambda x: self.range.set_values(min(int(round(x * 100)), self.range.hi), self.range.hi))
        self.e_spin.valueChanged.connect(
            lambda x: self.range.set_values(self.range.lo, max(int(round(x * 100)), self.range.lo)))

    def times(self):
        t0, t1 = self.s_spin.value(), self.e_spin.value()
        return (t0, t1) if t1 > t0 else (t1, t0)

    def set_times(self, t0, t1):
        lo, hi = int(round(max(0.0, t0) * 100)), int(round(min(self.dur, t1) * 100))
        lo, hi = min(lo, hi), max(lo, hi)
        self.range.set_values(lo, hi)  # the boxes follow
        self.s_spin.setValue(lo / 100)
        self.e_spin.setValue(hi / 100)

    def target_pos(self):
        """Where the card's word is in the sentence: the part in italics, else the word field,
        else the longest start of it found (言い張る -> 言い張っ, 鋭敏 in 鋭敏化)."""
        m = re.search(r"(?is)<(i|em)\b[^>]*>", self.html)
        if m:
            spans = html_map(self.html)[1]
            k = next((k for k, (s0, _) in enumerate(spans) if s0 >= m.end()), None)
            if k is not None:
                return k
        for f in (self.c.get("word_field", "word"), self.c.get("written_field", "word-as-written")):
            w = plain(self.note[f]) if f in self.note.keys() else ""
            for n in range(len(w), 0, -1):
                stem = w[:n]
                if n < len(w) and not re.search(r"[一-鿿々]", stem):
                    break
                k = self.text.find(stem)
                if k >= 0:
                    return k
        return None

    # speech recognition done: suggest the sentence that holds the word
    def _heard(self, fut):
        if self.closed or not self.isVisible():
            return
        try:
            self.words = fut.result()["words"]
        except Exception as e:
            self.status.setText(f"Speech recognition failed: {e}. The sliders still work.")
            return
        self.fit_btn.setEnabled(True)
        self.range.set_marks([int(round(w[0] * 100)) for w in self.words])
        if self.orig:
            self.status.setText("Already cut: the current cut is selected. Adjust it, select other text, "
                                "or Restore original.")
            return
        p = proposals().get(str(self.note.id)) if self.note.id else None
        if p:
            a, b = (p["a"], p["b"]) if self.text == p.get("full") else (self.text.find(p["text"]), -1)
            if a >= 0:
                b = b if b >= 0 else a + len(p["text"])
                cur = self.view.textCursor()
                cur.setPosition(a); cur.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
                self.view.setTextCursor(cur)
                self.fit(suggested="Proposed cut")
                return
        target = self.target_pos()
        if target is None:
            self.status.setText("Couldn't find the card's word in the sentence. Select text and Fit to selection.")
            return

        def done(f):
            if self.closed or not self.isVisible():
                return
            try:
                r = f.result()
            except Exception:
                r = {}
            if not r.get("cut"):
                self.status.setText("Short enough as it is. Select text and Fit to selection to cut anyway.")
                return
            cur = self.view.textCursor()
            cur.setPosition(r["a"]); cur.setPosition(r["b"], QTextCursor.MoveMode.KeepAnchor)
            self.view.setTextCursor(cur)
            self.fit(suggested=True)
        req = {"cmd": "span", "text": self.text, "target": target,
               "max": self.c.get("suggest_max_chars", 40), "min": self.c.get("suggest_min_chars", 10)}
        mw.taskman.run_in_background(lambda: WORKER.ask(req), done)

    def fit(self, suggested=False):
        cur = self.view.textCursor()
        a, b = cur.selectionStart(), cur.selectionEnd()
        if a == b or not self.words:
            tooltip("Select some of the sentence first")
            return
        self.status.setText("Finding it in the audio…")
        req = {"cmd": "fit", "text": self.text, "a": a, "b": b, "words": self.words}

        def done(f):
            if self.closed or not self.isVisible():
                return
            try:
                r = f.result()
            except Exception as e:
                self.status.setText(f"Couldn't place that text: {e}. Use the sliders.")
                return
            self.set_times(r["t0"] - self.c["pad_start"], r["t1"] + self.c["pad_end"])
            self.sel = (a, b)
            self.cut_text.setEnabled(True)
            self.cut_text.setChecked(True)
            low = " (only partly recognized, check by ear)" if r.get("coverage", 1) < 0.6 else ""
            what = suggested if isinstance(suggested, str) else ("Suggested cut" if suggested else "Fitted")
            self.status.setText(f"{what}: {r['t0']:.2f}–{r['t1']:.2f} s{low}")
        mw.taskman.run_in_background(lambda: WORKER.ask(req), done)

    def play(self, path):
        av_player.stop_and_clear_queue()
        av_player.play_file(path)

    def play_cut(self):
        if self.text_only:
            return
        t0, t1 = self.times()
        try:
            make_cut(self.src, t0, t1, self.tmp)
        except Exception as e:
            showWarning(f"ffmpeg failed: {e}")
            return
        self.play(self.tmp)

    def _apply(self, fields, add_tag=None, remove_tag=None):
        for k, v in fields.items():
            self.note[k] = v
        if self.note.id:
            for t in (TAG_CUT, TAG_KEPT):
                if t == remove_tag or (add_tag and t != add_tag):
                    self.note.remove_tag(t)
            if add_tag:
                self.note.add_tag(add_tag)
        if not self.editor:
            update_note(parent=mw, note=self.note).run_in_background()
        elif self.note.id:
            update_note(parent=self.editor.widget, note=self.note).success(
                lambda _: self.editor.loadNoteKeepingFocus()).run_in_background()
        else:
            self.editor.loadNoteKeepingFocus()

    def keep_as_is(self):
        """Queue: the card stays as it is, marked as looked at (clip-cut::kept, or still
        clip-cut::edited if it was cut before)."""
        self._apply({}, add_tag=TAG_CUT if self.orig else TAG_KEPT)
        self.go_next = True
        self.accept()

    def save_text(self):
        """No audio: the sentence becomes the selected part; the original is kept for Restore."""
        cur = self.view.textCursor()
        a, b = cur.selectionStart(), cur.selectionEnd()
        if a == b:
            tooltip("Select the part to keep first")
            return
        new = cut_html(self.html, a, b)
        c = self.c
        if new == self.current:  # nothing changed: same as Keep as is
            self.keep_as_is()
            return
        if self.note.id:
            d = originals()
            d.setdefault(str(self.note.id), {"audio": None, "sentence": self.html})
            save_originals(d)
        self._apply({c["sentence_field"]: new}, add_tag=TAG_CUT)
        tooltip("Sentence cut")
        self.go_next = True
        self.accept()

    def save(self):
        if self.text_only:
            self.save_text()
            return
        av_player.stop_and_clear_queue()
        t0, t1 = self.times()
        stem = os.path.splitext(self.src_name)[0]
        out = os.path.join(tempfile.gettempdir(), f"{stem}_cut{int(t0 * 1000)}-{int(t1 * 1000)}.mp3")
        try:
            make_cut(self.src, t0, t1, out)
        except Exception as e:
            showWarning(f"ffmpeg failed: {e}")
            return
        name = mw.col.media.add_file(out)
        c = self.c
        if self.note.id:
            d = originals()
            d.setdefault(str(self.note.id), {"audio": self.src_name, "sentence": self.html})
            try:
                keep_copy(d[str(self.note.id)]["audio"])
            except Exception as e:
                showWarning(f"Couldn't keep a copy of the original audio: {e}. Nothing was changed.")
                return
            save_originals(d)
        fields = {c["audio_field"]: f"[sound:{name}]"}
        if self.cut_text.isChecked() and self.sel:
            fields[c["sentence_field"]] = cut_html(self.html, *self.sel)
        self._apply(fields, add_tag=TAG_CUT)
        tooltip(f"Cut to {t1 - t0:.1f} s")
        self.go_next = True
        self.accept()

    def restore(self):
        av_player.stop_and_clear_queue()
        c = self.c
        fields = {c["sentence_field"]: self.orig["sentence"]}
        if self.orig.get("audio"):
            media_back(self.orig["audio"])
            fields[c["audio_field"]] = f"[sound:{self.orig['audio']}]"
        self._apply(fields, remove_tag=TAG_CUT)
        d = originals()
        d.pop(str(self.note.id), None)
        save_originals(d)
        tooltip("Original audio and sentence restored")
        self.go_next = "same"  # queue: the same card again, uncut, with its proposal
        self.accept()


def open_cutter(editor):
    note = editor.note
    c = cfg()
    if not note or note.note_type()["name"] != c["note_type"]:
        tooltip(f"Only for {c['note_type']} notes")
        return

    def show():
        m = re.search(r"\[sound:([^\]]+)\]", note[c["audio_field"]])
        orig = originals().get(str(note.id)) if note.id else None
        if orig:
            media_back(orig["audio"])
        src = orig["audio"] if orig else (m.group(1) if m else None)
        if src and not os.path.exists(os.path.join(mw.col.media.dir(), src)):
            src = None  # audio file missing: cut the text only
        Cutter(editor, note, src, orig).show()
    editor.call_after_note_saved(show)


def add_button(buttons, editor):
    sc = cfg().get("shortcut", "Ctrl+Meta+X")
    buttons.append(editor.addButton(icon=None, cmd="clip_cutter", func=open_cutter, label="✂",
                                    tip=f"Cut the sentence audio ({sc})", keys=sc))
    return buttons


# ---------------------------------------------------------------- background transcription

def prepare():
    c = cfg()
    nids = mw.col.find_notes(c["prepare_search"])
    media = mw.col.media.dir()
    paths = []
    for nid in nids:
        m = re.search(r"\[sound:([^\]]+)\]", mw.col.get_note(nid)[c["audio_field"]])
        if m and os.path.exists(os.path.join(media, m.group(1))):
            paths.append(os.path.join(media, m.group(1)))
    paths = list(dict.fromkeys(paths))
    tooltip(f"Clip cutter: transcribing {len(paths)} clips in the background")

    def work():
        done = 0
        for p in paths:
            try:
                if not WORKER.ask({"cmd": "cached", "path": p})["cached"]:
                    WORKER.ask({"cmd": "asr", "path": p})
            except Exception:
                pass
            done += 1
            if done % 50 == 0:
                mw.taskman.run_on_main(lambda d=done: tooltip(f"Clip cutter: {d}/{len(paths)} clips ready"))
        return done
    mw.taskman.run_in_background(work, lambda f: tooltip(f"Clip cutter: all {len(paths)} clips ready"))


def open_card(q, nid):
    """One card in the queue's window: an already cut card opens on its original audio."""
    c = cfg()
    media = mw.col.media.dir()
    try:
        note = mw.col.get_note(nid)
    except Exception:
        return False
    orig = originals().get(str(nid))
    if orig:
        media_back(orig.get("audio"))
        src = orig.get("audio")
    else:
        m = re.search(r"\[sound:([^\]]+)\]", note[c["audio_field"]])
        src = m.group(1) if m else None
    if src and not os.path.exists(os.path.join(media, src)):
        src = None  # no audio: the window cuts the sentence text only
    Cutter(None, note, src, orig, queue=q).show()
    return True


def open_next(q, step=1):
    """step 1: the next card (one you went back past, else the next untouched one with a
    proposal); -1: the one before; 0: the same card again."""
    if step == 0:
        if open_card(q, q["seen"][q["i"]]):
            return
        step = 1
    if step < 0:
        while q["i"] > 0:
            q["i"] -= 1
            if open_card(q, q["seen"][q["i"]]):
                return
        return
    while q["i"] + 1 < len(q["seen"]):
        q["i"] += 1
        if open_card(q, q["seen"][q["i"]]):
            return
    while q["pos"] < len(q["nids"]):
        nid = q["nids"][q["pos"]]
        q["pos"] += 1
        try:
            note = mw.col.get_note(nid)
        except Exception:
            continue
        if note.has_tag(TAG_CUT) or note.has_tag(TAG_KEPT):
            continue
        q["seen"].append(nid)
        q["i"] = len(q["seen"]) - 1
        if open_card(q, nid):
            return
    tooltip("No proposed cuts left")


def start_queue():
    """Tools > Clip cutter > Go through proposed cuts: one card after another, the proposed
    part already selected and fitted; Save & next, Keep as is & next, Back (as many steps as
    you like), or Stop. Cards you saved or kept are tagged clip-cut::edited / clip-cut::kept and
    skipped next time; remove the tag to put a card back in the queue."""
    done = set(mw.col.find_notes("tag:clip-cut"))
    nids = [int(k) for k in proposals() if int(k) not in done]
    nids = [n for n in nids if mw.col.db.scalar("select 1 from notes where id = ?", n)]
    if not nids:
        tooltip("No proposed cuts left")
        return
    open_next({"nids": nids, "pos": 0, "total": len(nids), "seen": [], "i": -1})


def setup_menu():
    m = QMenu("Clip cutter", mw)
    q = QAction("Go through proposed cuts", mw)
    q.triggered.connect(start_queue)
    m.addAction(q)
    a = QAction("Transcribe tagged cards in the background", mw)
    a.triggered.connect(prepare)
    m.addAction(a)
    mw.form.menuTools.addMenu(m)


gui_hooks.editor_did_init_buttons.append(add_button)
gui_hooks.main_window_did_init.append(setup_menu)
gui_hooks.profile_will_close.append(WORKER.close)
gui_hooks.profile_did_open.append(copy_all_originals)  # cuts saved before copies were kept
gui_hooks.profile_did_open.append(tag_cut_notes)  # and before cuts were tagged
