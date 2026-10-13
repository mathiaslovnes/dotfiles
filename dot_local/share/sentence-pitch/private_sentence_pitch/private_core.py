"""
Sentence pitch: a card's sentence with furigana, each word colored by its dictionary
pitch accent, and the pitch contour of the whole sentence drawn above the furigana.

Standard library only, so the same code runs inside Anki and from a terminal.

  words and readings  <- pyopenjtalk (analyze.py, run in its own Python)
  word colors         <- your own cards' pitch-accent-category first, then Yomitan
                         (/ankiFields), the same source the vocab cards were filled from
  contour, furigana   <- Suzuki-kun (OJAD), or pyopenjtalk's own prediction
"""
import difflib
import hashlib
import html
import json
import os
import re
import subprocess
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser

VERSION = 14  # bump to recolor every sentence (14: the card's word inside a compound: 社会|秩序)
# a fix that only changes some sentences: (version, text those sentences contain).
# Sentences colored before that version and containing the text are recolored.
FIXES = [(7, "何"), (9, "\n")]
DATA_V = max([VERSION] + [v for v, _ in FIXES])
CATS = ("heiban", "atamadaka", "nakadaka", "odaka", "kifuku")

# not colored: particles, auxiliaries (だ, です, た, ます ...), symbols, prefixes, suffixes,
# numbers, and grammar words written in kana (ている, てしまう, こと, よう, はず ...)
SKIP_POS = {"助詞", "助動詞", "記号", "接頭詞", "フィラー"}
SKIP_POS1 = {"接尾", "数"}
# only suffixes that mark personal names; さん and 様 also follow titles (司教様, 店員さん)
HONORIFICS = {"ちゃん", "くん", "君", "たん", "ちゃま"}
POTENTIAL = dict(zip("えけげせてねべめれ", "うくぐすつぬぶむる"))  # 出せる -> 出す
SMALL_KANA = set("ぁぃぅぇぉゃゅょゎゕゖァィゥェォャュョヮヵヶ")
DASHES = r"[―—─‐–-]"


class Unavailable(Exception):
    """Yomitan, Suzuki-kun or the analyzer is not reachable."""


# ---------------------------------------------------------------- text helpers

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "")


def clean(s):
    return html.unescape(strip_tags(s)).replace("\xa0", " ").strip()


def esc(s):
    return html.escape(s, quote=False)


def to_hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s or "")


def is_kana_char(c):
    return "ぁ" <= c <= "ゖ" or "ァ" <= c <= "ヺ" or c == "ー"


def is_kana(s):
    return bool(s) and all(is_kana_char(c) for c in s)


def exact_reading(s):
    """Comparable reading: hiragana, voicing kept, nasal か゚ counted as が."""
    s = re.sub(r"[(（][^)）]*only[)）]", "", s or "")
    s = re.sub(r"[\s]", "", s)
    s = unicodedata.normalize("NFD", to_hira(s))
    s = re.sub("([かきくけこ])\u309a", "\\1\u3099", s)
    return unicodedata.normalize("NFC", s)


def readings_of(field_value):
    """A reading field can hold several readings (、 , ・ /)."""
    parts = re.split(r"[、,・/／;；]", clean(field_value))
    return [r for r in (exact_reading(p) for p in parts) if r]


def first_cat(s):
    for part in re.split(r"[^a-z]+", clean(s).lower()):
        if part in CATS:
            return part
    return None


def split_morae(kana):
    out = []
    for c in kana:
        if c in SMALL_KANA and out:
            out[-1] += c
        else:
            out.append(c)
    return out


# ---------------------------------------------------------------- sentence field

BOLD_ON, BOLD_OFF = "\ue000", "\ue001"


def parse_sentence(raw, furigana=False, with_bold=False):
    """Field HTML -> (plain lines, text marked with <i> or None[, bold character
    positions per line]). <i> marks the card's word; bold marks names, shown without pitch."""
    m = re.search(r"(?is)<(i|em)\b[^>]*>(.*?)</\1>", raw or "")
    marked = clean(m.group(2)) if m else None
    raw = re.sub(r"[\r\n]+", "", raw or "")  # line breaks in the HTML source aren't shown
    s = re.sub(r"(?i)<(b|strong)\b[^>]*>", BOLD_ON, raw)
    s = re.sub(r"(?i)</(b|strong)\s*>", BOLD_OFF, s)
    s = re.sub(r"(?i)<br\s*/?>|</div>|</p>", "\n", s)
    s = html.unescape(strip_tags(s)).replace("\xa0", " ")
    if furigana:  # Anki furigana:  日本語[にほんご]を 勉強[べんきょう] -> 日本語を勉強
        s = re.sub(r" ?([^ \[\]\n]+)\[[^\]\n]*\]", r"\1", s)
        if marked:
            marked = re.sub(r" ?([^ \[\]]+)\[[^\]]*\]", r"\1", marked)
    lines, bolds, inside = [], [], False
    for ln in s.split("\n"):
        text, bold = "", set()
        for c in ln.strip():
            if c in (BOLD_ON, BOLD_OFF):
                inside = c == BOLD_ON
                continue
            if inside:
                bold.add(len(text))
            text += c
        text = text.strip()  # sentinels next to spaces
        if text:
            lines.append(text)
            bolds.append(bold)
    return (lines, marked, bolds) if with_bold else (lines, marked)


def source_hash(raw_sentence, written, word, target_cat, reading=""):
    key = json.dumps([VERSION, raw_sentence, written, word, target_cat, readings_of(reading)],
                     ensure_ascii=False)
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def stored_hash(pitch_field):
    m = re.search(r'data-h="([0-9a-f]+)"', pitch_field or "")
    return m.group(1) if m else None


def needs_fix(pitch_field, raw_sentence):
    """Colored before a fix that can change this sentence?"""
    m = re.search(r'data-v="(\d+)"', pitch_field or "")
    v = int(m.group(1)) if m else 0
    return any(v < fv and s in (raw_sentence or "") for fv, s in FIXES)


# ---------------------------------------------------------------- analyzer

class Analyzer:
    """pyopenjtalk process (analyze.py in the venv), started on first use."""

    def __init__(self, python, script):
        self.cmd, self.p = [python, script], None

    def run(self, texts):
        if self.p is None:
            try:
                self.p = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE, text=True, encoding="utf-8")
            except OSError as e:
                raise Unavailable(f"can't start {self.cmd[0]}: {e}")
        try:
            self.p.stdin.write(json.dumps(texts, ensure_ascii=False) + "\n")
            self.p.stdin.flush()
            line = self.p.stdout.readline()
        except OSError as e:
            raise Unavailable(f"analyzer stopped: {e}")
        if not line:
            raise Unavailable("analyzer stopped: " + self.p.stderr.read()[-800:])
        return json.loads(line)

    def close(self):
        if self.p is None:
            return
        try:
            self.p.stdin.close()
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


# ---------------------------------------------------------------- word categories

class Lookup:
    """Pitch category of a dictionary-form word.

    1. your cards (so a word has the same color as on its own vocab card)
    2. Yomitan: every entry with this spelling and reading; for a word in kana,
       every entry read that way.
    Candidates disagree -> the one matching pyopenjtalk's reading of the word on its
    own (if tiebreak is on), else no color.
    """

    def __init__(self, yomitan_url, cache=None):
        self.url = yomitan_url.rstrip("/") + "/ankiFields"
        self.cards = {}             # (word, reading) -> {cat}
        self.cards_by_word = {}     # word -> {cat}
        self.cards_by_reading = {}  # reading -> {cat}
        self.card_notes = {}        # (word, reading) -> {"cat (note type)"}
        self.card_readings = {}     # word -> {reading}
        self.cache = cache if cache is not None else {}  # word -> [[expression, reading, cats]]
        self.memo = {}
        self.lookups = 0
        self.lone = None  # (word, part of speech) -> category pyopenjtalk gives the word alone

    def add_card(self, word, reading_field, category, source=""):
        word, cat = clean(word), first_cat(category)
        if not word or not cat:
            return
        self.cards_by_word.setdefault(word, set()).add(cat)
        for r in readings_of(reading_field) or ([exact_reading(word)] if is_kana(word) else []):
            self.cards.setdefault((word, r), set()).add(cat)
            self.cards_by_reading.setdefault(r, set()).add(cat)
            self.card_readings.setdefault(word, set()).add(r)
            self.card_notes.setdefault((word, r), set()).add(f"{cat} ({source})" if source else cat)

    def conflicts(self):
        """Cards for the same word and reading with different categories."""
        return [f"{w} ({r}): " + ", ".join(sorted(self.card_notes[(w, r)]))
                for (w, r), cats in sorted(self.cards.items()) if len(cats) > 1]

    def ping(self):
        try:
            self._post({"text": "あ", "type": "term", "markers": ["expression"],
                        "maxEntries": 1, "includeMedia": False}, timeout=5)
        except Exception as e:
            raise Unavailable(f"Yomitan API not reachable ({e}). Is Brave open?")

    def _post(self, payload, timeout=30):
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def frequency(self, word, reading):
        """JPDB rank of this word read this way (smaller = more common), or None."""
        key = "\x00freq\x00" + word
        if key not in self.cache:
            try:
                res = self._post({"text": word, "type": "term", "markers": ["expression", "reading", "frequencies"],
                                  "maxEntries": 20, "includeMedia": False})
            except Exception as e:
                raise Unavailable(f"Yomitan lookup failed for {word}: {e}")
            self.lookups += 1
            out = []
            for e in res.get("fields", []):
                m = re.search(r"JPDB[^:<]*:\s*(\d+)(?![\d㋕])", e.get("frequencies") or "")
                out.append([clean(e.get("expression")), clean(e.get("reading")), int(m.group(1)) if m else None])
            self.cache[key] = out
        ranks = [f for expr, r, f in self.cache[key] if expr == word and exact_reading(r) == reading and f]
        return min(ranks) if ranks else None

    def knows(self, word, reading):
        """Is this a reading of this word, on your cards or in the dictionaries?"""
        return (word, reading) in self.cards or any(
            e[0] == word and exact_reading(e[1]) == reading for e in self.yomitan(word))

    def has_entry(self, word, with_pitch=False):
        return any(e[0] == word and (not with_pitch or first_cat(e[2])) for e in self.yomitan(word))

    def yomitan(self, word):
        if word not in self.cache:
            try:
                res = self._post({"text": word, "type": "term",
                                  "markers": ["expression", "reading", "pitch-accent-categories"],
                                  "maxEntries": 20, "includeMedia": False})
            except Exception as e:
                raise Unavailable(f"Yomitan lookup failed for {word}: {e}")
            self.lookups += 1
            self.cache[word] = [[clean(e.get("expression")), clean(e.get("reading")),
                                 clean(e.get("pitch-accent-categories"))]
                                for e in res.get("fields", [])]
        return self.cache[word]

    def positions(self, word, reading):
        """Accent positions the dictionaries give for this word and reading."""
        key = "\x00pos\x00" + word
        if key not in self.cache:
            try:
                res = self._post({"text": word, "type": "term",
                                  "markers": ["expression", "reading", "pitch-accent-positions"],
                                  "maxEntries": 20, "includeMedia": False})
            except Exception as e:
                raise Unavailable(f"Yomitan lookup failed for {word}: {e}")
            self.lookups += 1
            self.cache[key] = [[clean(e.get("expression")), clean(e.get("reading")),
                                clean(e.get("pitch-accent-positions"))] for e in res.get("fields", [])]
        out = []  # in the dictionaries' order: the first is the usual one
        for expr, r, p in self.cache[key]:
            if expr == word and (not reading or exact_reading(r) == reading):
                out += [int(x) for x in re.findall(r"\d+", p) if int(x) not in out]
        return out

    def category(self, word, reading, pos=None):
        """-> (category or None, source/reason)"""
        key = (word, reading, pos)
        if key not in self.memo:
            self.memo[key] = self._category(word, reading, pos)
        return self.memo[key]

    def _tiebreak(self, word, pos, cats, reason):
        if self.lone and is_kana(word):
            c = self.lone(word, pos)
            if c in cats:
                return c, "tiebreak"
        return None, reason

    def _category(self, word, reading, pos=None):
        kana = is_kana(word)
        # a card spelled exactly like this; then, for a word written in kana,
        # cards of any spelling read this way (それ -> your 其れ card)
        tiers = [self.cards.get((word, reading), set()) if reading else self.cards_by_word.get(word, set())]
        if kana:
            tiers.append(self.cards_by_reading.get(exact_reading(word), set()))
        for cats in tiers:
            if len(cats) == 1:
                return next(iter(cats)), "card"
            if len(cats) > 1:
                return self._tiebreak(word, pos, cats, "your cards disagree")

        entries = self.yomitan(word)
        cands = [e for e in entries
                 if e[0] == word or (kana and exact_reading(e[1]) == exact_reading(word))]
        if reading:
            cands = [e for e in cands if exact_reading(e[1]) == reading]
        cats = {first_cat(e[2]) for e in cands} - {None}
        if len(cats) == 1:
            return next(iter(cats)), "yomitan"
        if len(cats) > 1:
            return self._tiebreak(word, pos, cats, "dictionaries disagree")
        return None, "no pitch data" if cands else "not in dictionary"


def lone_category(analyzer, word, pos):
    """Category pyopenjtalk gives the word on its own, if it reads it as the same part of speech."""
    res = analyzer.run([word])[0]
    nodes = [n for n in res if n["mora_size"] > 0] if isinstance(res, list) else []
    if len(nodes) != 1 or nodes[0]["string"] != word or (pos and nodes[0]["pos"] != pos):
        return None
    acc, m = nodes[0]["acc"], nodes[0]["mora_size"]
    if acc == 0:
        return "heiban"
    if nodes[0]["pos"] in ("動詞", "形容詞"):
        return "kifuku"
    return "atamadaka" if acc == 1 else "odaka" if acc >= m else "nakadaka"


def deps_changed(lookup, entries):
    """Would any word of an already colored sentence get a different color now?"""
    return any(lookup.category(w, r, p)[0] != c for w, r, p, c in entries)


# ---------------------------------------------------------------- per-word facts

def is_content(n):
    if n["pos_group1"] == "非自立" and is_kana(n["string"]):
        return False
    return n["mora_size"] > 0 and n["pos"] not in SKIP_POS and n["pos_group1"] not in SKIP_POS1


def can_start(n):
    """Can an accent phrase begin with this word? (not a particle, auxiliary or suffix)"""
    return n["mora_size"] > 0 and n["pos"] not in ("助詞", "助動詞", "記号") and n["pos_group1"] != "接尾"


NOT_NAME = {"代名詞", "非自立"}
KIN = {"嬢", "兄", "姉", "坊", "爺", "婆", "母", "父"}  # (お)嬢ちゃん, 兄ちゃん: not names


def is_hira(s):
    return all("ぁ" <= c <= "ゖ" for c in s)


def nickname(run, lookup):
    """メガネ君, 吸血鬼ちゃん, 委員長ちゃん: an ordinary dictionary word (3+ characters, so
    not 撫子 or 月, which names read their own way), said as written: colored as usual."""
    s = "".join(n["string"] for n in run)
    if s in KIN:
        return True
    if lookup is None or len(s) < 3 or any(n["pos_group1"] == "固有名詞" for n in run):
        return False
    return lookup.has_entry(s, with_pitch=True)


def name_nodes(nodes, lookup=None):
    """Nouns right before ちゃん, くん ... are names: no color, furigana or contour, like a
    name in bold (お兄ちゃん and nicknames like メガネ君 excepted).
    Nouns before the honorific count while they could be part of a name: not a word with
    kana in it like 確か (確か君: 君 = きみ), and, before the last one, not 全部 / 普段 /
    場合 (副詞可能) or a word in hiragana (ふだん撫子ちゃん)."""
    out = set()
    for i, n in enumerate(nodes):
        if i == 0 or n["string"] not in HONORIFICS or n["pos"] != "名詞":
            continue
        j = i - 1
        while j >= 0:
            m = nodes[j]
            if m["string"] in ("々", "ヶ", "ケ"):
                j -= 1
                continue
            if m["pos"] != "名詞" or m["pos_group1"] in NOT_NAME or m["string"] in HONORIFICS:
                break  # (メガネ君君: the second 君 is きみ)
            if m["pos_group1"] == "形容動詞語幹" and not all(not is_hira(c) for c in m["string"]):
                break  # 確か
            if j < i - 1 and (m["pos_group1"] == "副詞可能" or is_hira(m["string"])):
                break
            j -= 1
        k = j + 1
        while k < i and nodes[k]["pos_group1"] == "接尾":
            k += 1  # a name doesn't start with a suffix (長 in 委員長 stays with 委員)
        if k == i or (j >= 0 and nodes[j]["pos"] == "接頭詞"):  # お兄ちゃん
            continue
        if nickname(nodes[k:i], lookup):
            continue
        out.update(range(k, i))
    return out


def merge_compounds(nodes, lookup):
    """Join words pyopenjtalk split but your dictionaries know as one word, so they're
    colored and phrased as one: compound verbs (討ち + 漏らし) whenever the dictionaries
    have them, other pairs (ナ + リ, 名詞 + 名詞) only if they also have its pitch."""
    nodes = list(nodes)
    i = 0
    while i + 1 < len(nodes):
        a, b = nodes[i], nodes[i + 1]
        verbs = a["pos"] == "動詞" and a.get("cform", "").startswith("連用") and b["pos"] == "動詞"
        nouns = a["pos"] == "名詞" and b["pos"] in ("名詞", "動詞", "形容詞")
        if (a["pos"] in ("名詞", "副詞") and a["pos_group1"] not in ("代名詞", "非自立", "数")
                and b["string"] in ("ずつ", "づつ") and node_kana(a) and node_kana(b)):  # 少し|ずつ
            whole = a["string"] + b["string"]
            kana = exact_reading(to_hira("".join(node_kana(a) + node_kana(b))))
            if any(e[0] == whole and first_cat(e[2]) and exact_reading(e[1]) == kana
                   for e in lookup.yomitan(whole)):
                nodes[i:i + 2] = [dict(a, string=whole, orig=whole, read=a["read"] + b["read"],
                                       pron=a["pron"] + b["pron"], mora_size=a["mora_size"] + b["mora_size"],
                                       pos="副詞" if a["pos"] == "副詞" else a["pos"], merged=True)]
                continue
        if (verbs or nouns) and is_content(a) and is_content(b) and node_kana(a) and node_kana(b):
            whole = a["string"] + (b["orig"] if b["orig"] not in ("", "*") else b["string"])
            if lookup.has_entry(whole, with_pitch=not verbs):
                nodes[i:i + 2] = [dict(b, string=a["string"] + b["string"], orig=whole,
                                       read=a["read"] + b["read"], pron=a["pron"] + b["pron"],
                                       mora_size=a["mora_size"] + b["mora_size"],
                                       acc=a["acc"], chain_flag=a["chain_flag"], merged=True)]
                continue
        i += 1
    return nodes


NANI_N = set("タチツテトダヂヅデドナヌネノラ")  # 何の 何で 何と 何だ 何なの 何て 何ら


def fix_nani(nodes):
    """Suzuki-kun reads 何 as なん everywhere. 何 alone: なん before t/d/n sounds (何の,
    何で, 何だ, 何て), before counters (何人, 何回) and in 何にも/何にせよ; なに everywhere
    else (何を, 何が, 何か, 何も, 何に使う, 何考えて, 何？). Words starting with 何
    (何より, 何一つ, 何やら, 何で, 何らか): pyopenjtalk's reading, which gets these right."""
    out = list(nodes)
    for i, n in enumerate(out):
        if not n["string"].startswith("何") or n.get("merged"):
            continue
        nxt = out[i + 1] if i + 1 < len(out) else None
        if n["string"] != "何":
            if is_kana(to_hira(n.get("read") or "")):
                out[i] = dict(n, forced=True)
            continue
        if n["pos"] != "名詞" or (n["pos_group1"] == "数" and nxt and nxt["pos_group1"] in ("数", "接尾")):
            continue
        after = out[i + 2]["string"] if i + 2 < len(out) else ""
        p = to_hira(nxt["pron"]) if nxt and nxt["mora_size"] > 0 else ""
        p = re.sub("[’']", "", p)
        if p[:1] == "に":
            nan = after.startswith(("も", "せ"))
        else:
            nan = bool(p) and p[0] in to_hira("".join(NANI_N))
        kana = "ナン" if nan else "ナニ"
        out[i] = dict(n, read=kana, pron=kana, forced=True)
    return out


def base_form(n):
    """(dictionary form, its reading in hiragana or None) of a pyopenjtalk node."""
    s, o = n["string"], n["orig"]
    if not o or o == "*":
        o = s
    r = to_hira(n.get("read") or "")
    if not is_kana(r):
        return o, None
    if n.get("ctype", "").startswith("カ変"):
        return o, "くる"
    if s == o:
        return o, exact_reading(r)
    p = 0
    while p < min(len(s), len(o)) and s[p] == o[p]:
        p += 1
    s_rest, o_rest = s[p:], o[p:]
    if (s_rest and not is_kana(s_rest)) or (o_rest and not is_kana(o_rest)):
        return o, None
    s_rest = to_hira(s_rest)
    if not r.endswith(s_rest):
        return o, None
    return o, exact_reading(r[:len(r) - len(s_rest)] + to_hira(o_rest))


ADJ_ENDING = {"連用テ接続": 1, "体言接続": 1, "連用ゴザイ接続": 1, "ガル接続": 0}


def dict_chars(n):
    """How many characters of the word to color: the dictionary part, not the conjugation
    (分かっ|た -> 分か, 高かっ|た -> 高, むつまじ|く)."""
    s, o = n["string"], n["orig"] if n["orig"] not in ("", "*") else n["string"]
    ct, cf = n.get("ctype", "*"), n.get("cform", "*")
    if s == o or ct == "*":
        return len(s)
    if ct.startswith("五段"):
        k = 1
    elif ct.startswith("一段"):
        k = 0 if cf.startswith(("未然", "連用")) else 1
    elif ct.startswith("形容詞"):
        k = ADJ_ENDING.get(cf, 2)
    else:
        p = 0
        while p < min(len(s), len(o)) and s[p] == o[p]:
            p += 1
        k = len(s) - p
    k = min(k, len(s))
    return len(s) - k if k == 0 or is_kana(s[-k:]) else len(s)


def node_kana(n):
    """The node's morae as hiragana, or None if they can't be shown one by one."""
    for k in ("read", "pron"):
        h = to_hira(n.get(k) or "")
        if is_kana(h):
            m = split_morae(h)
            if len(m) == n["mora_size"]:
                return m
    return None


def align(text, nodes):
    """Character span (start, end) of each node in text, or None.
    Tolerates pyopenjtalk's full-width conversion and characters it drops."""
    norm = [unicodedata.normalize("NFKC", c) for c in text]
    spans, pos = [], 0
    for n in nodes:
        s = unicodedata.normalize("NFKC", n["string"])
        found = None
        if s.strip():
            for start in range(pos, min(len(text), pos + 4)):
                i, j = start, 0
                while i < len(text) and j < len(s) and norm[i] and s.startswith(norm[i], j):
                    j += len(norm[i])
                    i += 1
                if j == len(s):
                    found = (start, i)
                    break
        spans.append(found)
        if found:
            pos = found[1]
    return spans


# ---------------------------------------------------------------- contour
# A line's contour is a list of items, whichever source it comes from:
#   {"kana", "h", "start", "owner"}  one mora: high? (None = don't draw), starts an
#                                    accent phrase?, index of the word it belongs to
#   {"punct"}                        punctuation / pause

def phrases(nodes):
    """pyopenjtalk accent phrases: [("p", [node indexes], accent) | ("x", node index)]."""
    items, cur = [], None
    for i, n in enumerate(nodes):
        if n["mora_size"] <= 0:
            items.append(("x", i))
            cur = None
            continue
        if cur is None or n["chain_flag"] != 1:
            cur = [i]
            items.append(("p", cur, n["acc"]))
        else:
            cur.append(i)
    return items


def levels(n_morae, acc):
    """High/low of each mora in an accent phrase (Tokyo pattern)."""
    acc = min(max(acc, 0), n_morae)
    return [(acc == 0 and k > 1) or (acc == 1 and k == 1) or (acc > 1 and 1 < k <= acc)
            for k in range(1, n_morae + 1)]


def openjtalk_morae(nodes, draw=True):
    """Readings (and, if draw, the contour) as pyopenjtalk predicts them."""
    items = []
    for g in phrases(nodes):
        if g[0] == "x":
            s = nodes[g[1]]["string"].strip()
            if s:
                items.append({"punct": s})
            continue
        _, idxs, acc = g
        lv = levels(sum(nodes[i]["mora_size"] for i in idxs), acc)
        k = 0
        for i in idxs:
            kana = node_kana(nodes[i])
            if not kana:
                k += nodes[i]["mora_size"]
                continue
            for piece in kana:
                items.append({"kana": piece, "h": lv[k] if draw else None, "start": k == 0, "owner": i})
                k += 1
    return items


# Suzuki-kun (OJAD prosody tutor, University of Tokyo)
OJAD_URL = "https://www.gavo.t.u-tokyo.ac.jp/ojad/phrasing/index"
OJAD_FORM = {"_method": "POST", "data[Phrasing][curve]": "advanced", "data[Phrasing][accent]": "advanced",
             "data[Phrasing][accent_mark]": "all", "data[Phrasing][estimation]": "crf",
             "data[Phrasing][analyze]": "true", "data[Phrasing][phrase_component]": "invisible",
             "data[Phrasing][param]": "invisible", "data[Phrasing][subscript]": "visible",
             "data[Phrasing][jeita]": "invisible"}
_ojad_last = [0.0]
stop = [False]  # set when Anki closes: stop between Suzuki-kun requests
OJAD_FORMAT = 2  # bump to drop cached results parsed by older code


class _MoraParser(HTMLParser):
    """Collects the mora and end-mark spans of one Suzuki-kun result row."""

    def __init__(self):
        super().__init__()
        self.items, self.depth, self.cur = [], 0, None

    def handle_starttag(self, tag, attrs):
        if tag != "span":
            return
        self.depth += 1
        cls = dict(attrs).get("class") or ""
        if self.cur is None:
            if re.search(r"\bmola_\d+", cls):
                self.cur = {"kana": "", "h": "accent_plain" in cls or "accent_top" in cls,
                            "top": "accent_top" in cls, "d": self.depth}
            elif "endmark" in cls:
                self.cur = {"punct": "", "d": self.depth}

    def handle_endtag(self, tag):
        if tag != "span":
            return
        if self.cur is not None and self.depth == self.cur["d"]:
            del self.cur["d"]
            self.items.append(self.cur)
            self.cur = None
        self.depth -= 1

    def handle_data(self, data):
        if self.cur is not None:
            self.cur["kana" if "kana" in self.cur else "punct"] += data.strip()


def parse_ojad(page):
    """Result page -> rows, one per group Suzuki-kun drew (it splits sentences at 、 too):
    {"text": that part of the sentence, "items": morae/punct with phrase ids}."""
    rows = []
    for chunk in re.split(r'<div class="phrasing_phrase_wrapper">', page)[1:]:
        body = re.search(r'<div class="phrasing_text">(.*?)</div>', chunk, re.S)
        if not body:
            continue
        p = _MoraParser()
        p.feed(body.group(1))
        morae = [it for it in p.items if "kana" in it]
        if not morae:
            continue
        ids = [int(x) for arr in re.findall(r"set_accent_curve_phrase\('[^']*',\d+,\[([\d,]*)\]", chunk)
               for x in arr.split(",") if x]
        if len(ids) != len(morae):  # derive: every new high stretch is a new phrase
            ids, pid, prev = [], 0, False
            for m in morae:
                pid += m["h"] and not prev
                ids.append(pid if m["h"] else 0)
                prev = m["h"]
        for m, pid in zip(morae, ids):
            m["pid"] = pid
        sub = re.search(r'<div class="phrasing_subscript">(.*?)</div>', chunk, re.S)
        rows.append({"text": clean(sub.group(1)) if sub else "", "items": p.items})
    return rows


OPEN_QUOTES, CLOSE_QUOTES = "「『“‘（(〈《【", "」』”’）)〉》】"


def ojad_key(line):
    """The text sent to Suzuki-kun. It ignores quotes and brackets, so 映画サークル“みそぎ”では
    would be read as one run: an opening quote becomes a pause (、), a closing one goes.
    Spaces and dashes are pauses in subtitles; Suzuki-kun drops spaces and reads dashes as ー,
    which glues the words around them into one (際 利益 -> さいりえき): both become 、."""
    line = re.sub(DASHES, " ", line)
    line = re.sub(r"(?<=[^\s、。！？!?…])[\s\u3000\xa0]+(?=\S)", "、", line.strip())
    out, straight = [], 0
    for c in line:
        if c in OPEN_QUOTES or (c == '"' and straight % 2 == 0):
            out.append("、" if out and out[-1] not in "、。！？ " else "")
        elif c not in CLOSE_QUOTES and c != '"':
            out.append(c)
        straight += c == '"'
    return "".join(out).strip()


def ojad_fetch(lines, min_interval=10.0, timeout=60):
    """One request for many lines; spaced at least min_interval seconds apart."""
    while time.monotonic() < _ojad_last[0] + min_interval:
        if stop[0]:
            raise Unavailable("stopped")
        time.sleep(0.5)
    if stop[0]:
        raise Unavailable("stopped")
    data = dict(OJAD_FORM)
    data["data[Phrasing][text]"] = "\n".join(lines)
    req = urllib.request.Request(OJAD_URL, data=urllib.parse.urlencode(data).encode(),
                                 headers={"User-Agent": "Mozilla/5.0 (personal Anki study add-on)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception as e:
        raise Unavailable(f"Suzuki-kun not reachable: {e}")
    finally:
        _ojad_last[0] = time.monotonic()
    return parse_ojad(page)


def ojad_rows(lines, min_interval=10.0, readings=None):
    """Rows for each line. Some lines (気が済むんだあ？) make Suzuki-kun return an error page
    for the whole request: then ask for each half separately, down to single lines."""
    readings = readings or [None] * len(lines)
    rows = ojad_fetch(lines, min_interval)
    if rows or len(lines) == 1:
        return assign_rows(lines, rows, readings)
    half = len(lines) // 2
    return (ojad_rows(lines[:half], min_interval, readings[:half])
            + ojad_rows(lines[half:], min_interval, readings[half:]))


def ojad_pending(jobs, cache, min_interval):
    """Seconds a batch would spend waiting on Suzuki-kun (0 if all its lines are cached)."""
    empty = set(cache.get("_empty", []))
    if cache.get("_format") == OJAD_FORMAT and all(
            not has_japanese(k) or cache.get(k) or k in empty
            for j in jobs for k in map(ojad_key, parse_sentence(j["raw"], j["furigana"])[0])):
        return 0.0
    return max(0.0, _ojad_last[0] + min_interval - time.monotonic()) + 3.0


def has_japanese(s):
    """Lines without any kana or kanji (an English word, ♪, ……) go wrong at Suzuki-kun:
    it skips them but not their caption, so every later line in the request gets the
    contour of the line after it."""
    return any(is_kana_char(c) or "一" <= c <= "鿿" or c in "々〆ヶ" for c in s or "")


def rows_match(rows, nodes):
    """Do Suzuki-kun's morae read roughly like pyopenjtalk's reading of the same line?"""
    oj = "".join(to_hira(it["kana"]) for r in rows for it in r["items"] if "kana" in it)
    ours = "".join(to_hira(n.get("read") or "") for n in nodes if n["mora_size"] > 0)
    if not oj or not ours:
        return True
    return difflib.SequenceMatcher(None, oj, ours, autojunk=False).ratio() >= 0.5


def _sig(s):
    """Letters and digits only, for matching Suzuki-kun's echo of the text to our lines."""
    return "".join(c for c in unicodedata.normalize("NFKC", s) if unicodedata.category(c)[0] in "LN")


def _follows(rk, ref, start):
    """Does Suzuki-kun's reading rk continue our reading ref at start? -> where it ends, or None."""
    sm = difflib.SequenceMatcher(None, rk, ref[start:start + 2 * len(rk) + 6], autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size]
    if not blocks or blocks[0].b > 3 or sum(b.size for b in blocks) < 0.6 * len(rk):
        return None
    return start + blocks[-1].b + blocks[-1].size


def assign_rows(lines, rows, readings=None):
    """Give each line its rows (Suzuki-kun splits at 。？！ and 、). With our readings of the
    lines (kana), rows are matched by what they read: a line Suzuki-kun can't analyze (え？,
    burger) gets no row but its caption still does, so the captions shift past it."""
    out = [[] for _ in lines]
    readings = readings or [None] * len(lines)
    if not all(readings):  # no readings: trust the captions
        sigs = [_sig(ln) for ln in lines]
        li, pos = 0, 0
        for row in rows:
            rs = _sig(row["text"])
            if not rs:
                continue
            for lj in range(li, min(len(lines), li + 4)):
                start = pos if lj == li else 0
                q = sigs[lj].find(rs, start)
                if q >= 0 and q - start <= 3:
                    out[lj].append(row)
                    li, pos = lj, q + len(rs)
                    break
        return out
    li, pos = 0, 0
    for row in rows:
        rk = "".join(to_hira(it["kana"]) for it in row["items"] if "kana" in it)
        if not rk:
            continue
        for lj in range(li, min(len(lines), li + 4)):
            end = _follows(rk, readings[lj], pos if lj == li else 0)
            if end is not None:
                out[lj].append(row)
                li, pos = lj, end
                break
    return out


def pack_rows(rows):
    """Compact form for the on-disk cache: [text, [[kana, 0 low/1 high/2 kernel, phrase] | [punct]]]."""
    return [[r["text"], [[it["punct"]] if "punct" in it else
                         [it["kana"], 2 if it["top"] else int(it["h"]), it["pid"]] for it in r["items"]]]
            for r in rows]


def unpack_rows(packed):
    return [{"text": t, "items": [{"punct": x[0]} if len(x) == 1 else
                                  {"kana": x[0], "h": x[1] > 0, "top": x[1] == 2, "pid": x[2]}
                                  for x in items]}
            for t, items in packed]


SPECIAL_MORAE = {"ー", "ん", "っ"}


def fix_special_kernels(morae):
    """Tokyo Japanese doesn't put the drop right after ー, ん or っ: when Suzuki-kun does
    (デー↘ンじん), move it back to the mora before (デ↘ーンじん). Returns how many moved."""
    moved = 0
    for k, m in enumerate(morae):
        j = k
        while m["top"] and to_hira(m["kana"]) in SPECIAL_MORAE and j > 0 and morae[j - 1]["row"] == m["row"]:
            prev = morae[j - 1]
            m["top"], m["h"] = False, False
            prev["top"], prev["h"], prev["pid"] = True, True, m["pid"]
            m, j = prev, j - 1
            moved += 1
    return moved


def _row_groups(rows, morae, ours, line, spans):
    """Split the alignment by Suzuki-kun's rows (one per stretch between punctuation): each
    row's morae only go to the words in that stretch of the line, so a name Suzuki-kun reads
    with more morae than pyopenjtalk (阿良々木くん、右腕) can't push its extra morae onto the
    next word. -> (row of each word, [(mora indexes, our indexes)] per row), or None if a row
    can't be found in the line."""
    if not line or spans is None or len(rows) < 2:
        return None
    if any(spans[i] is None for i in {o[1] for o in ours}):
        return None  # a word not found in the text (500 read as 五百): can't place it in a row
    flat = [(k, ch) for k, c in enumerate(line) for ch in unicodedata.normalize("NFKC", c)
            if unicodedata.category(ch)[0] in "LN"]
    sig = "".join(ch for _, ch in flat)
    starts, pos = [], 0
    for row in rows:
        rs = _sig(row.get("text", ""))
        if not rs:
            if any("kana" in it for it in row["items"]):
                return None  # Suzuki-kun didn't echo this row's text (‪ marks in the line)
            starts.append(None)
            continue
        p = sig.find(rs, pos)
        if p < 0:
            return None
        starts.append(flat[p][0])
        pos = p + len(rs)
    node_row = [0 if sp is None else
                max((r for r, st in enumerate(starts) if st is not None and st <= sp[0]), default=0)
                for sp in spans]
    return node_row, [([k for k, m in enumerate(morae) if m["row"] == r],
                       [k for k, o in enumerate(ours) if node_row[o[1]] == r]) for r in range(len(rows))]


def _assign(morae, ours):
    sm = difflib.SequenceMatcher(None, [to_hira(m["kana"]) for m in morae],
                                 [o[0] for o in ours], autojunk=False)
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        for a in range(a1, a2):
            if tag == "equal":
                o = ours[b1 + a - a1]
            elif tag == "replace":
                o = ours[b1 + (a - a1) * (b2 - b1) // (a2 - a1)]
                o = (o[0], o[1], False)
            else:
                continue
            morae[a]["owner"], morae[a]["wstart"] = o[1], o[2]


def ojad_morae(rows, nodes, stats=None, line=None, spans=None):
    """Contour from Suzuki-kun rows; each mora is tied to a pyopenjtalk word by aligning
    the two kana sequences (where the readings differ, proportionally)."""
    items, morae = [], []
    for r, row in enumerate(rows):
        for it in row["items"]:
            it = dict(it, row=r)
            items.append(it)
            if "kana" in it:
                morae.append(it)
    fixed = fix_special_kernels(morae)
    if stats is not None and fixed:
        stats["drops moved off ー/ん/っ"] = stats.get("drops moved off ー/ん/っ", 0) + 1

    ours = []  # (kana, node index, word can start a phrase here)
    for i, n in enumerate(nodes):
        for j, m in enumerate(node_kana(n) or []):
            ours.append((m, i, j == 0 and can_start(n)))
    if ours:
        _assign(morae, ours)  # the whole line at once: the most context
        split = _row_groups(rows, morae, ours, line, spans)
        for mi, oi in (split[1] if split else []):  # a row whose morae went to a word in another
            if any(split[0][morae[k].get("owner", 0)] != morae[k]["row"]   # row: align it alone
                   for k in mi if morae[k].get("owner") is not None):
                for k in mi:
                    morae[k].pop("owner", None)
                    morae[k].pop("wstart", None)
                _assign([morae[k] for k in mi], [ours[k] for k in oi])
        for k, m in enumerate(morae):  # extra morae only Suzuki-kun has: join the neighbor
            if "owner" not in m:  # (in the same row if it has one)
                near = [x for x in morae[k - 1::-1] if "owner" in x and x["row"] == m["row"]] if k else []
                near = near or [x for x in morae[k + 1:] if "owner" in x and x["row"] == m["row"]]
                near = near or ([x for x in morae[k - 1::-1] if "owner" in x] if k else [])
                near = near or [x for x in morae[k + 1:] if "owner" in x]
                if near:
                    m["owner"] = near[0]["owner"]
        for i, n in enumerate(nodes):  # readings set by a rule (fix_nani) win over Suzuki-kun's
            own = [m for m in morae if m.get("owner") == i]
            kana = node_kana(n) if n.get("forced") else None
            if kana and len(own) == len(kana):
                for m, k in zip(own, kana):
                    m["kana"] = k

    # phrase starts. Suzuki-kun numbers the high stretch of each phrase; the low mora
    # in front of a stretch belongs to it unless it ends the previous phrase.
    last_pid, run_end, run_kernel, row = None, -1, False, None
    for i, m in enumerate(morae):
        m["start"] = i == 0 or m["row"] != row
        if m["start"]:
            last_pid, run_end, run_kernel, row = None, -1, False, m["row"]
        if not m["h"]:
            continue
        if last_pid is not None and m["pid"] != last_pid:
            lo = run_end + 1
            if morae[i - 1]["h"]:
                m["start"] = True
            elif not run_kernel:  # previous phrase stayed high to its end: first word after it
                k = next((k for k in range(lo, i + 1) if morae[k].get("wstart")), None)
            else:  # the low mora before the rise, or the rise itself, where a word starts
                k = next((k for k in (i - 1, i) if k >= lo and morae[k].get("wstart")), None)
                if k is None:
                    k = next((k for k in range(i, lo - 1, -1) if morae[k].get("wstart")), None)
            if not morae[i - 1]["h"] and k is not None:
                morae[k]["start"] = True
        if m["pid"] != last_pid:
            run_kernel = False
        last_pid, run_end = m["pid"], i
        run_kernel = run_kernel or m["top"]
    return items


LONE_POS = {"名詞", "副詞"}
NOT_LONE = {"数", "接尾", "非自立", "代名詞"}
MIMETIC_USE = {"に", "だ", "な", "の", "で", "です", "する", "させる", "できる"}


def mimetic(s):
    """バラバラ, ぶらぶら, ピカピカ: the same two morae or more, twice."""
    k = to_hira(s)
    return len(k) >= 4 and len(k) % 2 == 0 and k[:len(k) // 2] == k[len(k) // 2:]


def is_katakana(s):
    return bool(s) and all("ァ" <= c <= "ヺ" or c == "ー" for c in s)


def dictionary_accents(items, nodes, cats, lookup, bold, stats):
    """Suzuki-kun guesses each word's accent from context and sometimes gets a plain word
    wrong (一蓮托生 as いち|れんたくしょう, すべて flattened before 吹き飛ぶ). For a noun or
    adverb that stands on its own (not part of a compound, not a number or suffix), with one
    accent in the dictionary that matches its color, draw that accent: the word starts its
    own phrase, its particles follow it, and the next word starts a new phrase."""
    by = {}
    for k, m in enumerate(items):
        if "kana" in m and m.get("owner") is not None:
            by.setdefault(m["owner"], []).append(k)
    for i, n in enumerate(nodes):
        cat = cats[i]
        if (i in bold or not cat or cat == "kifuku" or n["pos"] not in LONE_POS
                or n["pos_group1"] in NOT_LONE or i not in by):
            continue
        prev = nodes[i - 1] if i else None
        nxt = nodes[i + 1] if i + 1 < len(nodes) else None
        if prev is not None and (prev["pos"] in ("名詞", "接頭詞") and prev["mora_size"] > 0):
            continue  # compound (運命共同体) or prefix: Suzuki-kun knows better
        adverb = n["pos"] == "副詞" or n["pos_group1"] == "副詞可能"
        if nxt is not None and nxt["mora_size"] > 0 and (
                nxt["pos"] in ("名詞", "形容詞") or (nxt["pos"] == "動詞" and not adverb)):
            continue  # noun + noun / adjective / verb is often one word (かっこ悪い, 頼りなげ)
        nw = next((x for x in nodes[i + 1:] if x["pos_group1"] != "空白"), None)
        if n["pos_group1"] == "副詞可能" and nw is not None and (
                nw["pos"] in ("形容詞", "副詞") or nw["pos_group1"] == "形容動詞語幹"):
            continue  # 一番深い, 一番好き, 今すぐ: used as an adverb, often not the noun's accent
        word, reading = base_form(n)
        if (all("ぁ" <= c <= "ゖ" for c in n["string"]) and (word, reading) not in lookup.cards
                and not (adverb and n["mora_size"] >= 3)):
            continue  # a word in hiragana counts if it's one of your cards or an adverb like
            # すべて (not がれ in みやがれ, ど in ど…どれ)
        if n["pos"] == "名詞" and prev is not None and prev["pos"] == "副詞":
            continue  # いつも通り
        if is_katakana(n["string"]) and (n["mora_size"] < 2 or (prev is not None and is_katakana(prev["string"]))):
            continue  # a piece of a katakana word pyopenjtalk split (ヤンデ|レ)
        if mimetic(n["string"]) and nxt is not None and (
                nxt["string"] in MIMETIC_USE or base_form(nxt)[0] in MIMETIC_USE):
            continue  # バラバラに, ブラブラさせる, ピカピカの: flat in that use, Suzuki-kun hears it
        ks = by[i]
        kana = [to_hira(items[k]["kana"]) for k in ks]
        if any(items[k]["h"] is None for k in ks):
            continue  # no contour here
        if kana != (node_kana(n) or []):  # read otherwise than pyopenjtalk: only if the color
            heard = exact_reading("".join(kana))  # is that reading's (行手 as ゆきて, your card)
            if lookup.category(word, heard, n["pos"])[0] != cat:
                continue
            reading = heard
        size = len(ks)
        if cat == "heiban":
            acc = 0
        elif cat == "atamadaka":
            acc = 1
        elif cat == "odaka":
            if nxt is not None and nxt["string"] == "の":
                continue  # odaka + の often loses its accent (男の子): leave it to Suzuki-kun
            acc = size
        else:  # nakadaka: the dictionary's position (its first, if it gives several)
            pos = [p for p in lookup.positions(word, reading) if 1 < p < size]
            if not pos:
                continue
            acc = pos[0]
        accepted = {acc} | {p for p in lookup.positions(word, reading) if 0 <= p <= size}
        prev_m = None
        for k in range(ks[0] - 1, -1, -1):
            if "punct" in items[k]:
                break  # a pause before it
            if "kana" in items[k]:
                prev_m = items[k]
                break
        initial = (prev_m is None or items[ks[0]].get("start") or not prev_m.get("h")
                   or prev_m.get("row") != items[ks[0]].get("row"))
        # a phrase starts low (unless the accent is on its first mora); inside a phrase that
        # is still high (あの人, 私の本), the word stays high up to its accent
        want = levels(size, acc) if initial else [acc == 0 or k < acc for k in range(size)]
        follow = []  # particles after it, up to the next word
        j = i + 1
        while j < len(nodes) and nodes[j]["pos"] in ("助詞", "助動詞") and j in by:
            follow += by[j]
            j += 1
        have = [items[k]["h"] for k in ks]
        if have == want and all(items[k]["h"] == (acc == 0) for k in follow[:1]):
            continue  # Suzuki-kun already says so
        if any(have in (levels(size, a), [a == 0 or k < a for k in range(size)]) for a in accepted):
            continue  # Suzuki-kun picked another accent the dictionaries also accept (クラス)
        for k, h in zip(ks, want):
            items[k]["h"], items[k]["top"] = h, False
        if acc:
            items[ks[acc - 1]]["top"] = True
        if initial:
            items[ks[0]]["start"] = True
        for k in follow:
            items[k]["h"], items[k]["top"], items[k]["start"] = acc == 0, False, False
        if acc and j < len(nodes) and j in by:  # after a drop, a word that rises again
            nk = by[j]                           # starts its own phrase
            if items[nk[0]]["h"] or (len(nk) > 1 and items[nk[1]]["h"]):
                items[nk[0]]["start"] = True
                if len(nk) > 1 and items[nk[0]]["h"] and items[nk[1]]["h"]:
                    items[nk[0]]["h"] = False
        stats["dictionary accents"] = stats.get("dictionary accents", 0) + 1
        stats.setdefault("dictionary accent words", []).append(n["string"])


def mora_classes(items):
    """Line classes: h/l, plus the vertical stroke where the pitch rises (up) or falls (dn)
    inside an accent phrase."""
    prev = None
    for m in items:
        if "kana" not in m or m["h"] is None:
            prev = None
            continue
        if m.get("start"):
            prev = None
        lv = "h" if m["h"] else "l"
        m["cls"] = lv + (" up" if prev == "l" and lv == "h" else "") + (" dn" if prev == "h" and lv == "l" else "")
        prev = lv


# ---------------------------------------------------------------- colors

def heard_readings(items, nodes):
    """{word index: reading} where Suzuki-kun read a word that doesn't conjugate otherwise
    than pyopenjtalk (右腕: みぎうで, not うわん). The furigana show Suzuki-kun's reading."""
    by = {}
    for m in items:
        if "kana" in m and m.get("owner") is not None:
            by.setdefault(m["owner"], []).append(to_hira(m["kana"]))
    out = {}
    for i, n in enumerate(nodes):
        o = n["orig"] if n["orig"] not in ("", "*") else n["string"]
        if i in by and n["string"] == o and not is_kana(o) and not n.get("forced"):
            heard, ours = exact_reading("".join(by[i])), exact_reading(to_hira("".join(node_kana(n) or [])))
            if heard and heard != ours:
                out[i] = heard
    return out


def word_categories(nodes, lookup, target_nodes, target_word, target_cat, stats, deps, bold=(), heard=None):
    cats = [None] * len(nodes)
    content = [i for i, n in enumerate(nodes) if is_content(n)]
    names = name_nodes(nodes, lookup) | set(bold)
    override = set()
    if target_cat:
        override = {i for i in target_nodes if i in content and base_form(nodes[i])[0] == target_word}
        tc = [i for i in target_nodes if i in content]
        if not override and len(tc) == 1 and not (
                nodes[tc[0]].get("merged") and target_word in nodes[tc[0]]["string"]
                and nodes[tc[0]]["string"] != target_word):
            override = set(tc)  # (not a compound around the card's word: 社会秩序 has its own accent)
    for i in content:
        if i in override:
            cats[i] = target_cat
            stats["target"] = stats.get("target", 0) + 1
            continue
        if i in names:
            stats["names"] = stats.get("names", 0) + 1
            continue
        n = nodes[i]
        word, reading = base_form(n)
        if heard and i in heard and reading:
            if keep_heard(nodes, i) or voiceless(heard[i]) == voiceless(reading):
                # Suzuki-kun's reading if it has an accent (睡眠不足: ぶそく), else pyopenjtalk's
                # (田舎暮らし: the dictionary has くらし, not ぐらし)
                c = heard[i] if lookup.category(word, heard[i], n["pos"])[0] else reading
            else:
                c = pick_reading(word, n["pos"], heard[i], reading, lookup)
            if c != reading:  # color it as read in the furigana (or as on your card)
                reading = c
                stats["colored as Suzuki-kun read it"] = stats.get("colored as Suzuki-kun read it", 0) + 1
        cat, why = lookup.category(word, reading, n["pos"])
        deps.append([word, reading, n["pos"], cat])
        if (not cat and n["pos"] == "動詞" and n["ctype"].startswith("一段")
                and len(word) > 2 and word[-1] == "る" and word[-2] in POTENTIAL):
            # potential form missing from the dictionaries: same category as its verb
            r = (reading[:-2] + POTENTIAL[reading[-2]]
                 if reading and len(reading) > 2 and reading[-2] in POTENTIAL else None)
            w2 = word[:-2] + POTENTIAL[word[-2]]
            c2, why2 = lookup.category(w2, r, "動詞")
            deps.append([w2, r, "動詞", c2])
            if c2:
                cat, why = c2, why2
        cats[i] = cat
        if not cat and n["pos_group1"] == "固有名詞":
            stats["names"] = stats.get("names", 0) + 1
            continue
        stats[why] = stats.get(why, 0) + 1
        if not cat:
            stats.setdefault("uncolored", []).append(f"{word} ({reading or '?'}): {why}")
    return cats


def find_target(lines, spans_per_line, nodes_per_line, marked, written, word):
    """-> (line index, set of node indexes) of the card's word in the sentence."""
    for t in (marked, written, word):
        if not t:
            continue
        for li, line in enumerate(lines):
            a = line.find(t)
            if a < 0:
                continue
            b = a + len(t)
            hit = {i for i, sp in enumerate(spans_per_line[li]) if sp and sp[0] < b and sp[1] > a}
            if hit:
                return li, hit
    for li, nodes in enumerate(nodes_per_line):  # conjugated and not written as given
        hit = {i for i, n in enumerate(nodes) if is_content(n) and base_form(n)[0] == word}
        if hit:
            return li, {min(hit)}
    return None, set()


# ---------------------------------------------------------------- rendering
# Every piece of text is a unit: a furigana row (empty for kana) over the text.
# Contour morae sit in the furigana row for kanji and on the kana themselves; the
# stylesheet draws both at the same height above the furigana row.

def text_segments(text):
    """[(start, text, needs furigana)]: kana one mora at a time, anything else in runs."""
    segs, i = [], 0
    while i < len(text):
        j = i + 1
        if is_kana_char(text[i]):
            while j < len(text) and text[j] in SMALL_KANA:
                j += 1
            segs.append((i, text[i:j], False))
        else:
            while j < len(text) and not is_kana_char(text[j]):
                j += 1
            segs.append((i, text[i:j], True))
        i = j
    return segs


def fit(segs, morae):
    """Morae for each segment: a kana segment is its own mora, a kanji run takes 1 or more.
    None if the reading doesn't fit the text."""
    ks = [to_hira(m["kana"]) for m in morae]

    def go(si, mi):
        if si == len(segs):
            return [] if mi == len(ks) else None
        _, s, kanji = segs[si]
        if not kanji:  # ー matches the vowel Suzuki-kun reads for it (ほーう: ほ う う)
            if mi < len(ks) and (ks[mi] == to_hira(s) or (s == "ー" and ks[mi] in "あいうえおー")):
                rest = go(si + 1, mi + 1)
                return None if rest is None else [[mi]] + rest
            return None
        for end in range(mi + 1, len(ks) + 1):
            rest = go(si + 1, end)
            if rest is not None:
                return [list(range(mi, end))] + rest
        return None

    return go(0, 0)


def mo(m, text=None, color=None):
    cls = " ".join(x for x in ("mo", m.get("cls"), color) if x)
    return f'<span class="{cls}">{esc(to_hira(m["kana"]) if text is None else text)}</span>'


def unit(base, rt="", first=None, fc=0, bc=0):
    """fc, bc: furigana and base characters, when the furigana is longer than the base:
    it is then set a little smaller (card.css) instead of spreading the word apart."""
    ps = " ps" if first is not None and first.get("start") and first.get("cls") else ""
    long_ = f' data-o="1" style="--fc:{fc};--bc:{bc}"' if fc and bc and fc > 2 * bc else ""
    return f'<span class="u{ps}"{long_}><span class="rt">{rt}</span><span class="rb">{base}</span></span>'


def colored(text, color):
    return f'<span class="{color}">{esc(text)}</span>' if color and text else esc(text)


def render_plain(text):
    return [" " if part.isspace() else unit(esc(part)) for part in re.findall(r"\s+|\S+", text)]


def render_piece(text, morae, color=None, dlen=0):
    """One word (or a stretch the analyzer didn't cover) as a list of units."""
    if not morae:
        if not color:
            return render_plain(text)
        return [unit(colored(text[:dlen], color) + esc(text[dlen:]))]
    segs = text_segments(text)
    fitted = fit(segs, morae)
    if fitted is None:  # reading doesn't fit the text: furigana over the whole word
        base = colored(text[:dlen], color) + esc(text[dlen:])
        rt_color = color if color and dlen else None
        return [unit(base, "".join(mo(m, color=rt_color) for m in morae), morae[0])]
    out, run, run_first = [], [], None

    def flush():
        nonlocal run, run_first
        if run:
            out.append(unit("".join(run), first=run_first))
        run, run_first = [], None

    for (start, s, kanji), idx in zip(segs, fitted):
        col = color if color and start < dlen else None
        if kanji:
            flush()
            out.append(unit(colored(s, col), "".join(mo(morae[k], color=col) for k in idx), morae[idx[0]],
                            fc=sum(len(morae[k]["kana"]) for k in idx), bc=len(s)))
        else:
            m = morae[idx[0]]
            if m.get("start") and run:
                flush()
            if not run:
                run_first = m
            run.append(mo(m, s, col))
    flush()
    return out


def render_gap(text, morae):
    if not morae or not text.strip():
        return render_plain(text)
    lead, core_, trail = re.match(r"(\s*)(.*?)(\s*)$", text, re.S).groups()
    return ([" "] if lead else []) + render_piece(core_, morae) + ([" "] if trail else [])


WB = ""  # token: a new word group (bunsetsu) starts here


def starts_group(nodes, i):
    """Can a line break before this word? Not inside a word and its particles, endings and
    helpers (状況|に, 回転|する|ように, 食べ|て|いる), nor after a prefix or an opening quote."""
    n, prev = nodes[i], nodes[i - 1] if i else None
    if not can_start(n) or n["pos_group1"] in ("非自立", "接尾"):
        return n["string"] in OPEN_QUOTES
    if prev is None:
        return True
    if prev["pos"] == "接頭詞" or prev["string"] in OPEN_QUOTES:
        return False
    if n["pos"] == "動詞" and n["orig"] in ("する", "できる") and prev["pos"] == "名詞":
        return False  # 回転する
    return True


def group_phrases(tokens):
    """Wrap each word with its particles and endings in a group, so lines break only
    between such groups; an accent phrase may continue on the next line."""
    out, cur, inside = [], [], False

    def close():
        if cur:
            out.append(f'<span class="w">{"".join(cur)}</span>')
            cur.clear()

    for tok in tokens:
        if tok == WB:
            if not inside:
                close()
            continue
        if tok == " ":
            if not inside:
                close()
                out.append(" ")
                continue
        if tok == "<i>":
            inside = True
        elif tok == "</i>":
            inside = False
        cur.append(tok)
    close()
    return "".join(out)


def render_line(line, nodes, spans, items, cats, dlens, target, bold=()):
    by_node = {}
    for m in items:
        if "kana" in m and m.get("owner") is not None:
            by_node.setdefault(m["owner"], []).append(m)
    target = {i for i in target if spans[i]}
    first, last = (min(target), max(target)) if target else (None, None)
    out, pos, pending = [], 0, []
    for i, n in enumerate(nodes):
        if not spans[i]:  # e.g. ２人 read as 二人: its reading goes over the original text
            pending += by_node.get(i, [])
            continue
        a, b = spans[i]
        if a > pos or pending:
            out += render_gap(line[pos:a], pending)
            pending = []
        if starts_group(nodes, i):
            out.append(WB)
        if i == first:
            out.append("<i>")
        if i in bold:
            out.append(unit(f"<b>{esc(line[a:b])}</b>"))
        else:
            out += render_piece(line[a:b], by_node.get(i, []), cats[i], dlens[i])
        if i == last:
            out.append("</i>")
        pos = b
    if pos < len(line) or pending:
        out += render_gap(line[pos:], pending)
    return f'<div class="sl">{group_phrases(out)}</div>'


RARER = 5  # Suzuki-kun's reading this many times rarer than pyopenjtalk's: take pyopenjtalk's


def voiceless(s):
    return unicodedata.normalize("NFC", "".join(
        c for c in unicodedata.normalize("NFD", s or "") if c not in "\u3099\u309a"))


def keep_heard(nodes, i):
    """Words where Suzuki-kun's reading stands even when pick_reading would overrule it:
    - part of a word pyopenjtalk split, which Suzuki-kun reads whole: after a noun or prefix
      ending in kanji (全|弾 ぜんだん, 説得|力ない せっとくりょく, 傷害|女), or one kanji before
      kana that aren't particles (弱|すぎ よわすぎ)
    - names and their pieces (明智, 阿良々|木): neither reads those reliably."""
    n = nodes[i]
    if not n["string"] or is_kana_char(n["string"][0]):
        return False
    if n["pos_group1"] == "固有名詞":
        return True
    near = [nodes[k] for k in (i - 1, i + 1) if 0 <= k < len(nodes)]
    if i >= 2 and nodes[i - 1]["string"] in ("々", "ヶ", "ケ"):
        near.append(nodes[i - 2])
    if any(m["pos_group1"] == "固有名詞" for m in near):
        return True
    if i > 0:
        prev = nodes[i - 1]
        if prev["pos"] in ("名詞", "接頭詞") and prev["mora_size"] > 0 and prev["string"] \
                and not is_kana_char(prev["string"][-1]):
            return True
    if len(n["string"]) == 1 and i + 1 < len(nodes):
        nxt = nodes[i + 1]
        if nxt["mora_size"] > 0 and is_kana_char(nxt["string"][0]) and nxt["pos"] not in ("助詞", "助動詞"):
            return True
    return False


def pick_reading(word, pos, s, p, lookup):
    """Suzuki-kun read the word s, pyopenjtalk p (they differ). -> the reading to use.
    Suzuki-kun reads from context and is usually right (そんな風: ふう, 王の下で: もと), except
    - a reading with no accent in the dictionaries and not on a card (行手 as ぎょうて, 鏡 as
      きょう): your card's reading if you have one card reading for the word, else pyopenjtalk's
    - a reading far rarer than pyopenjtalk's (素振り: すぶり, JPDB rank 42602 vs 4774)."""
    if voiceless(s) == voiceless(p):
        return s  # rendaku: 暮らし as ぐらし in 田舎暮らし, 不足 as ぶそく in パワー不足
    cards = lookup.card_readings.get(word, set())
    if s in cards and p not in cards:
        return s
    p_ok = bool(p) and (p in cards or bool(lookup.category(word, p, pos)[0]))
    if not (s in cards or lookup.category(word, s, pos)[0]):
        if len(cards) == 1:
            return next(iter(cards))
        return p if p_ok else s
    if p_ok:
        fs, fp = lookup.frequency(word, s), lookup.frequency(word, p)
        if fs and fp and fs >= RARER * fp:
            return p
    return s


def reading_splices(line, nodes, rows, lookup, bold=(), card_fix=None):
    """[(start, end, kana)]: words Suzuki-kun read otherwise than they should be read
    (pick_reading), to send to it again in kana so the furigana and contour fit."""
    nodes = fix_nani(merge_compounds(nodes, lookup))
    spans = align(line, nodes)
    items = ojad_morae(rows, nodes, None, line, spans)
    heard = heard_readings(items, nodes)
    skip = name_nodes(nodes, lookup) | {i for i, sp in enumerate(spans) if sp and any(k in bold for k in range(*sp))}
    out = []
    for i, s in heard.items():
        sp, n = spans[i], nodes[i]
        if i in skip or sp is None or not is_content(n) or keep_heard(nodes, i):
            continue
        if card_fix and sp[0] < card_fix[1] and card_fix[0] < sp[1]:
            continue  # the card's word: its own reading fix
        word, p = base_form(n)
        if not p:
            continue
        c = pick_reading(word, n["pos"], s, p, lookup)
        if c and c != s and fit(text_segments(line[sp[0]:sp[1]]), [{"kana": m} for m in split_morae(c)]):
            out.append((sp[0], sp[1], c))
    return out


def card_reading_fix(job, lines, analyses, lookup):
    """{line index: (start, end, reading)}: the card's word, where the sentence has it as
    written on the card (巻), is read as its reading field says (かん, not まき)."""
    readings = readings_of(job.get("reading", ""))
    word = clean(job["word"])
    if not readings or not word or is_kana(word):
        return {}
    marked = parse_sentence(job["raw"], job["furigana"])[1]
    if marked and marked != word:
        return {}  # the sentence has another form of the word (読んで): leave it
    for li, (line, nodes) in enumerate(zip(lines, analyses)):
        a = line.find(word)
        if a < 0 or not isinstance(nodes, list):
            continue
        b = a + len(word)
        nodes = fix_nani(merge_compounds(nodes, lookup))
        spans = align(line, nodes)
        cover = [i for i, sp in enumerate(spans) if sp and a <= sp[0] and sp[1] <= b]
        if not cover or spans[cover[0]][0] != a or spans[cover[-1]][1] != b:
            return {}
        have = exact_reading("".join(to_hira(nodes[i].get("read") or "") for i in cover))
        good = [r for r in readings if fit(text_segments(word), [{"kana": m} for m in split_morae(r)])]
        if not good:
            return {}  # a reading that doesn't fit the word's kana (手に取るように): skip
        if have in good:  # pyopenjtalk reads it right; Suzuki-kun is checked once it answers
            return {li: (a, b, have, False)}
        return {li: (a, b, good[0], True)}
    return {}


def ojad_word_reading(rows, line, nodes, lookup, a, b):
    """How Suzuki-kun read the text between a and b."""
    nodes = fix_nani(merge_compounds(nodes, lookup))
    spans = align(line, nodes)
    cover = {i for i, sp in enumerate(spans) if sp and a <= sp[0] and sp[1] <= b}
    items = ojad_morae(rows, nodes)
    return exact_reading("".join(to_hira(m["kana"]) for m in items if "kana" in m and m.get("owner") in cover))


def apply_reading_fix(line, nodes, fix):
    """Make the card's word one word with the reading from its card."""
    a, b, reading = fix[:3]
    spans = align(line, nodes)
    cover = [i for i, sp in enumerate(spans) if sp and a <= sp[0] and sp[1] <= b]
    if not cover or spans[cover[0]][0] != a or spans[cover[-1]][1] != b:
        return nodes
    kata = "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in reading)
    first = nodes[cover[0]]
    word = dict(first, string=line[a:b], orig=line[a:b], read=kata, pron=kata,
                mora_size=len(split_morae(reading)), forced=True)
    return nodes[:cover[0]] + [word] + nodes[cover[-1] + 1:]


def render_note(raw_sentence, written, word, target_cat, analyses, lookup, furigana=False,
                contour_rows=None, reading_fix=None, reading=""):
    """-> (html, stats, deps). analyses: pyopenjtalk words per line. contour_rows:
    Suzuki-kun rows per line, or None to use pyopenjtalk's own contour.
    deps: the lookups behind the colors, to notice when one of them changes."""
    lines, marked, bolds = parse_sentence(raw_sentence, furigana, with_bold=True)
    stats, deps = {}, []
    nodes_per_line, spans_per_line = [], []
    for line, nodes in zip(lines, analyses):
        if isinstance(nodes, dict):  # analyzer error for this line
            stats["analyzer errors"] = stats.get("analyzer errors", 0) + 1
            nodes = []
        nodes = fix_nani(merge_compounds(nodes, lookup))
        if reading_fix and len(nodes_per_line) in reading_fix:
            nodes = apply_reading_fix(line, nodes, reading_fix[len(nodes_per_line)])
            stats["read as on the card"] = stats.get("read as on the card", 0) + 1
        nodes_per_line.append(nodes)
        spans_per_line.append(align(line, nodes))
        stats["unaligned"] = stats.get("unaligned", 0) + sum(
            1 for n, sp in zip(nodes, spans_per_line[-1]) if sp is None and n["string"].strip())

    target_cat = first_cat(target_cat)
    t_line, t_nodes = find_target(lines, spans_per_line, nodes_per_line, marked, clean(written), clean(word))
    stats["target found"] = 1 if t_nodes else 0

    out = []
    for li, (line, nodes, spans) in enumerate(zip(lines, nodes_per_line, spans_per_line)):
        target = t_nodes if li == t_line else set()
        bold = {i for i, sp in enumerate(spans) if sp and any(k in bolds[li] for k in range(*sp))}
        # names: in bold, or before ちゃん / くん (not the card's word): no color, furigana or pitch
        bold |= name_nodes(nodes, lookup) - set(target)
        heard = {}
        if contour_rows is None:
            items = openjtalk_morae(nodes)
        elif contour_rows[li]:
            items = ojad_morae(contour_rows[li], nodes, stats, line, spans)
            heard = heard_readings(items, nodes)
        else:  # no contour: furigana only
            items = openjtalk_morae(nodes, draw=False)
            stats["lines without contour"] = stats.get("lines without contour", 0) + 1
        cats = word_categories(nodes, lookup, target, clean(word), target_cat, stats, deps, bold, heard)
        if contour_rows is not None and contour_rows[li]:
            dictionary_accents(items, nodes, cats, lookup, bold, stats)
        hidden = set(bold)  # names: no pitch, nor for the ちゃん / particles after them
        for i in sorted(bold):
            j = i + 1
            while j < len(nodes) and j not in bold and (
                    nodes[j]["pos"] in ("助詞", "助動詞")
                    or (nodes[j]["string"] in HONORIFICS and nodes[j]["pos_group1"] in ("接尾", "代名詞"))):
                hidden.add(j)
                j += 1
        for m in items:
            if m.get("owner") in hidden:
                m["h"] = None
        mora_classes(items)
        out.append(render_line(line, nodes, spans, items, cats, [dict_chars(n) for n in nodes], target, bold))

    h = source_hash(raw_sentence, written, word, target_cat, reading)
    return f'<div class="sp" data-h="{h}" data-v="{DATA_V}">{"".join(out)}</div>', stats, deps


def mix_rows(first, kana):
    """Rows of a line asked again with some words in kana: the new rows where a word was
    given in kana, the first answer everywhere else (Suzuki-kun may read the rest of the
    line a little differently the second time). An incomplete second answer: the first."""
    if len(kana) < len(first):
        return first
    if len(kana) != len(first) or all(not r["text"] for r in kana):
        return kana
    return [b if a["text"] != b["text"] else a for a, b in zip(first, kana)]


def process_batch(jobs, analyzer, lookup, contour="ojad", ojad_interval=10.0, ojad_cache=None):
    """jobs: dicts with raw, written, word, cat, furigana -> [(html, stats, deps)].
    One analyzer call per batch, and one Suzuki-kun request for the lines it hasn't seen."""
    if lookup.lone is None:
        lookup.lone = lambda w, pos: lone_category(analyzer, w, pos)
    parsed = [parse_sentence(j["raw"], j["furigana"], with_bold=True) for j in jobs]
    inputs = [p[0] for p in parsed]
    flat = [ln for lines in inputs for ln in lines]
    bolds = [b for p in parsed for b in p[2]]
    res = analyzer.run(flat) if flat else []
    # the card's word: when pyopenjtalk reads it otherwise than the card, Suzuki-kun gets it
    # in kana right away; otherwise only if Suzuki-kun misreads it too (徒に as とに)
    fixes, flat_fix, k = [], [], 0
    for j, lines in zip(jobs, inputs):
        fix = card_reading_fix(j, lines, res[k:k + len(lines)], lookup)
        fixes.append(fix)
        flat_fix += [fix.get(li) for li in range(len(lines))]
        k += len(lines)

    def with_reading(ln, f):
        return ln[:f[0]] + f[2] + ln[f[1]:]
    sent = [with_reading(ln, f) if f and f[3] else ln for ln, f in zip(flat, flat_fix)]
    per_line = None
    if contour == "ojad" and flat:
        cache = ojad_cache if ojad_cache is not None else {}
        if cache.get("_format") != OJAD_FORMAT:
            cache.clear()
            cache["_format"] = OJAD_FORMAT
        keys = [ojad_key(ln) for ln in sent]
        nodes_of = {k: nodes for k, nodes in zip(keys, res) if isinstance(nodes, list)}

        def ok(k, packed):
            return k not in nodes_of or rows_match(unpack_rows(packed), nodes_of[k])

        empty = set(cache.get("_empty", []))  # lines Suzuki-kun really had nothing for

        def fetch(keys):
            for k in keys:
                if not has_japanese(k):
                    cache[k] = []  # nothing for Suzuki-kun to read
                elif k in cache and (not ok(k, cache[k]) or (cache[k] == [] and k not in empty)):
                    del cache[k]  # belongs to another line, or lost to one: ask again
            missing = [k for k in dict.fromkeys(keys) if k not in cache]
            if missing:
                readings = [to_hira("".join(n.get("read") or "" for n in nodes_of.get(k, []) if n["mora_size"] > 0))
                            for k in missing]
                for k, rows in zip(missing, ojad_rows(missing, ojad_interval, readings)):
                    packed = pack_rows(rows)
                    cache[k] = packed if ok(k, packed) else []  # still wrong: no contour
                    if not cache[k]:
                        empty.add(k)
                cache["_empty"] = sorted(empty)

        fetch(keys)
        again = []
        for x, f in enumerate(flat_fix):
            if f and not f[3] and isinstance(res[x], list) and has_japanese(keys[x]):
                rows = cache.get(keys[x])  # nothing at all (徒に) or a misread word: try in kana
                heard = ojad_word_reading(unpack_rows(rows), flat[x], res[x], lookup, f[0], f[1]) if rows else ""
                if heard != f[2]:
                    flat_fix[x] = f[:3] + (True,)
                    keys[x] = ojad_key(with_reading(flat[x], f))
                    nodes_of.setdefault(keys[x], res[x])
                    again.append(keys[x])
        if again:
            fetch(again)
        # other words Suzuki-kun misread (行手 as ぎょうて, 素振り as すぶり): ask again with them in kana
        before, again = list(keys), []
        for x, ln in enumerate(flat):
            rows = cache.get(keys[x])
            if not rows or not isinstance(res[x], list):
                continue
            f = flat_fix[x] if flat_fix[x] and flat_fix[x][3] else None
            spl = reading_splices(ln, res[x], unpack_rows(rows), lookup, bolds[x], f)
            if spl:
                text = ln
                for a, b, kana in sorted(spl + ([f[:3]] if f else []), reverse=True):
                    text = text[:a] + kana + text[b:]
                keys[x] = ojad_key(text)
                nodes_of.setdefault(keys[x], res[x])
                again.append(keys[x])
        if again:
            fetch(again)
        per_line = []
        for x, k in enumerate(keys):
            rows = unpack_rows(cache[k]) if cache.get(k) else []
            if k != before[x]:
                rows = mix_rows(unpack_rows(cache[before[x]]), rows)
            per_line.append(rows)
    out, k = [], 0
    for j, lines in zip(jobs, inputs):
        fix = {li: f for li, f in enumerate(flat_fix[k:k + len(lines)]) if f and f[3]}
        an = res[k:k + len(lines)]
        rows = per_line[k:k + len(lines)] if per_line is not None else None
        k += len(lines)
        out.append(render_note(j["raw"], j["written"], j["word"], j["cat"], an, lookup, j["furigana"], rows,
                               fix, j.get("reading", "")))
    return out


# ---------------------------------------------------------------- bookkeeping

def load_cache(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cache(path, cache):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def merge_stats(total, stats):
    for k, v in stats.items():
        if isinstance(v, list):
            total.setdefault(k, []).extend(v)
        else:
            total[k] = total.get(k, 0) + v


def format_report(n_notes, total, left=0, conflicts=()):
    colored_ = {k: total.get(k, 0) for k in ("card", "yomitan", "target", "tiebreak")}
    reasons = {k: total.get(k, 0) for k in ("your cards disagree", "dictionaries disagree",
                                           "no pitch data", "not in dictionary")}
    n_words = sum(colored_.values()) + sum(reasons.values())
    pct = f"{100 * sum(colored_.values()) / n_words:.0f}%" if n_words else "-"
    lines = [f"{n_notes} sentences processed" + (f", {left} left for later" if left else ""),
             f"{n_words} content words: {pct} colored",
             f"  from the card's own word: {colored_['target']}",
             f"  from your other cards:    {colored_['card']}",
             f"  from Yomitan:             {colored_['yomitan']}",
             f"  ties broken by pyopenjtalk's reading: {colored_['tiebreak']}",
             "  uncolored: " + ", ".join(f"{k} {v}" for k, v in reasons.items()),
             f"names left uncolored: {total.get('names', 0)}",
             f"card's word found in its sentence: {total.get('target found', 0)}/{n_notes}",
             f"words that couldn't be matched to the text: {total.get('unaligned', 0)}",
             f"sentence lines without a contour: {total.get('lines without contour', 0)}",
             f"lines where a drop was moved off ー/ん/っ: {total.get('drops moved off ー/ん/っ', 0)}",
             f"analyzer errors: {total.get('analyzer errors', 0)}"]
    if conflicts:
        lines += ["", f"Cards for the same word and reading with different categories ({len(conflicts)}):"]
        lines += [f"  {c}" for c in conflicts]
    lines += ["", "Most common uncolored words:"]
    for w, c in Counter(total.get("uncolored", [])).most_common(40):
        lines.append(f"  {c:4}  {w}")
    return "\n".join(lines)
