"""Pure text logic (no Anki imports), so it can be tested and run outside Anki."""
import html
import re

KANA_H = "ぁ-ゖ"
KANA_K = "ァ-ヺー"
KANJI = "一-龯々〆ヶ"
# a kanji name may run straight into one of these (槙島君, 四宮家, ヤン提督 is katakana so fine anyway)
HON_KANJI = "君様殿卿氏伯家先輩生隊艦軍公王帝"
HONORIFICS = ("さん", "くん", "ちゃん", "さま", "君", "様", "殿", "氏", "先輩", "先生", "卿")
MIN_LEN = 2
SKIP = re.compile(r"(?is)<b>.*?</b>|<i>.*?</i>|<ruby>.*?</ruby>|<[^>]+>|&[#\w]+;")
BOLD = re.compile(r"(?is)<b>(.*?)</b>")


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).replace("\xa0", " ").strip()


def names_in(field_html):
    """Names you bolded in a sentence, honorifics trimmed (<b>槙島君</b> -> 槙島)."""
    out = set()
    for b in BOLD.findall(field_html or ""):
        n = plain(b)
        for h in HONORIFICS:
            if n.endswith(h) and len(n) > len(h):
                n = n[: -len(h)]
                break
        if len(n) >= MIN_LEN and not re.search(r"\s", n):
            out.add(n)
    return out


def _pattern(name):
    e = re.escape(name)
    if re.fullmatch(f"[{KANA_K}・･＝]+", name):
        return f"(?<![{KANA_K}]){e}(?![{KANA_K}])"
    if re.fullmatch(f"[{KANA_H}]+", name):
        return f"(?<![{KANA_H}]){e}"
    return f"(?<![{KANJI}]){e}(?:(?=[{HON_KANJI}])|(?![{KANJI}]))"


def compile_names(names):
    names = sorted(set(names), key=len, reverse=True)
    if not names:
        return None
    return re.compile("|".join(_pattern(n) for n in names))


def bold(field_html, rx):
    """Bold every unbolded occurrence; leaves existing <b>, the card's <i> word, ruby and tags alone."""
    if not rx or not field_html:
        return field_html
    out, pos = [], 0
    for m in SKIP.finditer(field_html):
        out.append(rx.sub(lambda x: f"<b>{x.group(0)}</b>", field_html[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(rx.sub(lambda x: f"<b>{x.group(0)}</b>", field_html[pos:]))
    return "".join(out).replace("</b><b>", "")  # 光月 + おでん -> one bold run


def unbold(field_html, name):
    return re.sub(r"(?is)<b>(" + re.escape(name) + r")</b>", r"\1", field_html or "")
