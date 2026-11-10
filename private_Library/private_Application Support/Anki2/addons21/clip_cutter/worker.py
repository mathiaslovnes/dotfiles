"""Runs in its own Python (cutvenv), never inside Anki: speech recognition and text-to-audio alignment.

Protocol: one JSON request per line on stdin, one JSON answer per line on stdout.
  {"cmd": "asr", "path": ...}                         -> {"words": [[start, end, text], ...], "duration": s}
  {"cmd": "fit", "text": ..., "a": i, "b": j, "words"} -> {"t0": s, "t1": s, "coverage": 0..1}
  {"cmd": "suggest", "lines": [...], "target": i}     -> {"kept": [line indexes]}
  {"cmd": "span", "text": ..., "target": i, "max", "min"} -> {"cut": bool, "a": i, "b": j}
"""
import difflib
import json
import os
import re
import subprocess
import sys

import fugashi
import numpy as np

CACHE, MODEL, FFMPEG = sys.argv[1], sys.argv[2], sys.argv[3]
tagger = fugashi.Tagger()
model = None


def hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def kana_chars(text):
    """kana reading of text, and for each kana the index of the text character it came from"""
    out, idx, pos = [], [], 0
    for t in tagger(text):
        a = text.find(t.surface, pos)
        a = pos if a < 0 else a
        k = t.feature.kana if t.feature.kana not in (None, "*") else t.surface
        for c in re.sub(r"[^ぁ-ゖー]", "", hira(k)):
            out.append(c)
            idx.append(a)
        pos = a + len(t.surface)
    return "".join(out), idx


def asr(path):
    key = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", os.path.basename(path)) + f".{MODEL}.json")
    if os.path.exists(key):
        with open(key, encoding="utf-8") as f:
            return json.load(f)
    global model
    if model is None:
        from faster_whisper import WhisperModel
        model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    pcm = subprocess.run([FFMPEG, "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    segs, _ = model.transcribe(audio, language="ja", word_timestamps=True, beam_size=5)
    res = {"words": [[round(w.start, 3), round(w.end, 3), w.word] for s in segs for w in (s.words or [])],
           "duration": round(len(audio) / 16000, 3)}
    with open(key, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)
    return res


def fit(text, a, b, words):
    asr_k, asr_w = [], []
    for wi, (_, _, wt) in enumerate(words):
        for c in kana_chars(wt)[0]:
            asr_k.append(c)
            asr_w.append(wi)
    sub_k, sub_idx = kana_chars(text)
    ka = next((i for i, ci in enumerate(sub_idx) if ci >= a), None)
    kb = max((i for i, ci in enumerate(sub_idx) if ci < b), default=None)
    if ka is None or kb is None or kb < ka or not asr_k:
        raise ValueError("nothing to match in the selection")
    sm = difflib.SequenceMatcher(None, sub_k, "".join(asr_k), autojunk=False)
    pairs = [(m.a + d, m.b + d) for m in sm.get_matching_blocks() for d in range(m.size)]
    inside = [p for p in pairs if ka <= p[0] <= kb]
    if not inside:
        raise ValueError("couldn't find the selected text in the audio")
    t0 = words[asr_w[inside[0][1]]][0]
    t1 = words[asr_w[inside[-1][1]]][1]
    return {"t0": t0, "t1": t1, "coverage": round(len(inside) / (kb - ka + 1), 2)}


END = re.compile(r"[。！？!?」』…‥]$")
CONT = re.compile(r"[―⸺—─、,，]$")
FINAL = {"よ", "ね", "な", "か", "ぞ", "ぜ", "わ", "さ", "の", "かな", "かね", "っけ", "なあ", "ねえ", "よね"}


def ends_sentence(line):
    line = line.strip()
    if not line or END.search(line):
        return True
    if CONT.search(line):
        return False
    toks = list(tagger(line))
    if not toks:
        return True
    t = toks[-1]
    f = t.feature
    if f.pos1 == "助詞" and t.surface not in FINAL:
        return False
    if f.pos1 in ("動詞", "形容詞", "助動詞") and (f.cForm or "").startswith(("連用", "未然")):
        return False
    return True


def standalone(text):
    toks = list(tagger(text))
    return len(text) >= 12 and any(t.feature.pos1 in ("動詞", "形容詞", "助動詞") or t.feature.pos2 == "形状詞" for t in toks)


def suggest(lines, target):
    sents, cur = [], []
    for i, ln in enumerate(lines):
        cur.append(i)
        if ends_sentence(ln):
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    k = next((j for j, s in enumerate(sents) if target in s), 0)
    a = k
    while a > 0 and not standalone("".join(lines[i] for s in sents[a:k + 1] for i in s)):
        a -= 1
    return {"kept": [i for s in sents[a:k + 1] for i in s]}


def has_pred(text):
    return any(t.feature.pos1 in ("動詞", "形容詞", "助動詞") or t.feature.pos2 == "形状詞" for t in tagger(text))


CONJ = {"が", "て", "で", "けど", "けれど", "けれども", "から", "ので", "し", "ば", "のに", "ても", "でも", "つつ", "ながら"}


def segments(text, maxlen):
    """Subtitle lines (split at spaces and line breaks); a line longer than maxlen (book text)
    is split again after punctuation (、。！？…―」)."""
    out = []
    for m in re.finditer(r"[^ 　\n​]+", text):
        a, b = m.start(), m.end()
        if b - a <= maxlen:
            out.append((a, b))
            continue
        s = a
        for p in re.finditer(r"[、。！？!?…‥―─」』]+", text[a:b]):
            e = a + p.end()
            if e > s and e < b:
                out.append((s, e))
                s = e
        out.append((s, b))
    return out


def clause_end(seg):
    """Does the clause end with this line? Not after a case particle, の linking two nouns
    (大学に入ってからの), a prefix or an adnominal (その)."""
    toks = list(tagger(seg))
    if not toks:
        return True
    last = toks[-1]
    if last.feature.pos1 in ("連体詞", "接頭辞"):
        return False
    if last.surface == "の" and last.feature.pos2 == "格助詞":
        return False
    return ends_sentence(seg)


def soft_end(seg):
    """A natural pause even if the clause goes on: after が, て, けど, から ... (展開したが)."""
    toks = list(tagger(re.sub(r"[、…―─]+$", "", seg)))
    return bool(toks) and toks[-1].surface in CONJ and toks[-1].feature.pos1 == "助詞"


def span(text, target, maxlen=40, minlen=10):
    """Suggested cut around the card's word (target = its position in text). Lines are kept
    whole: the line with the word and the rest of its clause (電脳と義体によって + より高度な
    能力の獲得を追求したあげく); under minlen characters, more lines, from the side the clause
    continues on (大学に入ってからの + 怠惰で無為な日々). A clause that doesn't finish within
    maxlen stops at its last natural pause (…展開したが, not …展開したが その).
    -> {"cut": False} when the whole text is short enough or nothing shorter makes sense."""
    segs = segments(text, maxlen)
    if not segs:
        return {"cut": False}

    def size(i, j):
        return len(re.sub(r"\s", "", text[segs[i][0]:segs[j][1]]))

    if size(0, len(segs) - 1) <= maxlen:
        return {"cut": False}
    t = next((i for i, (a, b) in enumerate(segs) if a <= target < b), None)
    if t is None:
        t = min(range(len(segs)), key=lambda i: abs(segs[i][0] - target))
    ends = [clause_end(text[a:b]) for a, b in segs]
    soft = [ends[k] or soft_end(text[a:b]) for k, (a, b) in enumerate(segs)]
    i = j = t

    def finish_clause(i, j):
        while j + 1 < len(segs) and not ends[j] and size(i, j + 1) <= maxlen:
            j += 1
        return j

    j = finish_clause(i, j)
    while size(i, j) < minlen:
        left_ok = i > 0 and size(i - 1, j) <= maxlen
        right_ok = j + 1 < len(segs) and size(i, j + 1) <= maxlen
        if left_ok and (not ends[i - 1] or not right_ok):
            i -= 1
        elif right_ok:
            j = finish_clause(i, j + 1)
        else:
            break
    if not ends[j]:
        k = max((k for k in range(t, j + 1) if soft[k]), default=None)
        if k is not None:
            j = k
    if i == 0 and j == len(segs) - 1:
        return {"cut": False}
    return {"cut": True, "a": segs[i][0], "b": segs[j][1]}


def main():
    os.makedirs(CACHE, exist_ok=True)
    for line in sys.stdin:
        try:
            r = json.loads(line)
            if r["cmd"] == "asr":
                out = asr(r["path"])
            elif r["cmd"] == "fit":
                out = fit(r["text"], r["a"], r["b"], r["words"])
            elif r["cmd"] == "suggest":
                out = suggest(r["lines"], r["target"])
            elif r["cmd"] == "span":
                out = span(r["text"], r["target"], r.get("max", 40), r.get("min", 10))
            elif r["cmd"] == "cached":
                out = {"cached": os.path.exists(os.path.join(CACHE, re.sub(r"[^\w.-]", "_", os.path.basename(r["path"])) + f".{MODEL}.json"))}
            else:
                out = {"error": "unknown command"}
        except Exception as e:
            out = {"error": f"{type(e).__name__}: {e}"}
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
