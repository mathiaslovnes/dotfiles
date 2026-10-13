#!/usr/bin/env python3
"""
Turn the list definitions of the former Eminent V2.4 notes into plain lines, so they
follow the card's own alignment:
  <ul><li>reform</li><li>renewal</li></ul>                    -> reform<br>renewal
  <ol><li><ul><li>gap</li><li>space</li></ul></li><li>…</ol>  -> 1. gap; space<br>2. …
  a single-sense <ol> is treated like a plain list.
Empty items and &nbsp; at the ends of items are dropped; formatting inside items is kept.
Only notes that were Eminent are touched (read from the pre-conversion backup); a field
with text next to the list or broken HTML is listed and left alone.

Safety: every change goes to lists_log.tsv before the next note; MODE = "revert" restores
the old field (unless you edited it since). Needs Anki open (AnkiConnect).
Keep read_eminent_backup.py and crop_eminent_pictures.py in the same folder.
"""

import json
import os
import re
import time
from html.parser import HTMLParser

import crop_eminent_pictures as crop  # anki(), eminent_notes()

# ---------------- config ----------------
NOTE_TYPE = "subs2srs"
DEF_FIELD = "definition"
MODE = "convert"  # "dry-run", "convert" or "revert"
JOINER = "<br>"  # "; " would put them on one line instead
# ----------------------------------------

LOG_FILE = "lists_log.tsv"
SENSE_JOINER = "; "  # synonyms inside one numbered sense: "1. gap; space"
BLOCKS = {"div", "ul", "ol", "li"}


class Node:
    def __init__(self, tag):
        self.tag, self.children = tag, []


class Tree(HTMLParser):
    """Tiny tree of div/ul/ol/li; every other tag and all text is kept as raw markup."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node("root")
        self.stack = [self.root]
        self.broken = False

    def handle_starttag(self, tag, attrs):
        if tag in BLOCKS:
            node = Node(tag)
            self.stack[-1].children.append(node)
            self.stack.append(node)
        else:
            self.stack[-1].children.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in BLOCKS:
            if len(self.stack) == 1 or self.stack[-1].tag != tag:
                self.broken = True
            else:
                self.stack.pop()
        else:
            self.stack[-1].children.append(f"</{tag}>")

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_entityref(self, name):
        self.stack[-1].children.append(f"&{name};")

    def handle_charref(self, name):
        self.stack[-1].children.append(f"&#{name};")


class Odd(Exception):
    pass


def tidy(s):
    """Strip whitespace, &nbsp; and stray <br> from both ends."""
    return re.sub(r"^(?:\s|&nbsp;|<br\s*/?>)+|(?:\s|&nbsp;|<br\s*/?>)+$", "", s)


def blank(child):
    return isinstance(child, str) and not tidy(child)


def inline(node):
    """One line from an <li>: its text, with any list inside joined by SENSE_JOINER."""
    out = []
    for c in node.children:
        if isinstance(c, str):
            out.append(c)
        elif c.tag in ("ul", "ol"):
            items = [tidy(inline(li)) for li in c.children if not blank(li)]
            if any(
                not isinstance(li, Node) or li.tag != "li"
                for li in c.children
                if not blank(li)
            ):
                raise Odd
            out.append(" " + SENSE_JOINER.join(i for i in items if i))
        else:  # div inside an item
            out.append(" " + inline(c))
    return tidy("".join(out))


def list_lines(node):
    items = [c for c in node.children if not blank(c)]
    if any(not isinstance(c, Node) or c.tag != "li" for c in items):
        raise Odd  # text between the <li>s
    if node.tag == "ol" and len(items) > 1:  # numbered senses: one line each
        lines = [inline(li) for li in items]
        return [f"{k}. {t}" for k, t in enumerate((t for t in lines if t), 1)]
    if node.tag == "ol":  # a single sense: same as a plain list
        return block_lines(items[0])
    return [t for t in (inline(li) for li in items) if t]


def block_lines(node):
    """Lines from a container (field, div, single <li>) that holds only lists/divs."""
    kids = [c for c in node.children if not blank(c)]
    if kids and all(isinstance(c, Node) for c in kids):
        lines = []
        for c in kids:
            lines += list_lines(c) if c.tag in ("ul", "ol") else block_lines(c)
        return lines
    if node.tag == "li":
        return [inline(node)]
    raise Odd  # text next to the list


def to_lines(value):
    """Return the converted value, or None if the field has a shape this doesn't handle."""
    tree = Tree()
    tree.feed(value)
    tree.close()
    if tree.broken or len(tree.stack) != 1:
        return None
    try:
        lines = block_lines(tree.root)
    except Odd:
        return None
    return JOINER.join(lines) if lines else None


def revert():
    if not os.path.exists(LOG_FILE):
        raise SystemExit(f"No {LOG_FILE} here, nothing to revert.")
    entries = {}
    with open(LOG_FILE, encoding="utf-8") as fh:
        for line in fh:
            nid, old, new = line.rstrip("\n").split("\t")
            entries[int(nid)] = (json.loads(old), json.loads(new))
    ids, restored, edited = list(entries), 0, 0
    for i in range(0, len(ids), 200):
        for n in crop.anki("notesInfo", notes=ids[i : i + 200]):
            if not n or "noteId" not in n:
                continue
            old, new = entries[n["noteId"]]
            if n["fields"][DEF_FIELD]["value"] != new:
                edited += 1
                continue
            crop.anki(
                "updateNoteFields", note={"id": n["noteId"], "fields": {DEF_FIELD: old}}
            )
            restored += 1
    os.rename(LOG_FILE, LOG_FILE + f".reverted-{int(time.time())}")
    print(f"Restored {restored}; {edited} left alone because they were edited since.")


def main():
    if MODE == "revert":
        return revert()
    if MODE not in ("dry-run", "convert"):
        raise SystemExit('MODE must be "dry-run", "convert" or "revert"')
    ids = list(crop.eminent_notes())
    log = open(LOG_FILE, "a", encoding="utf-8") if MODE == "convert" else None
    converted, shown, odd = 0, 0, []
    for i in range(0, len(ids), 200):
        for n in crop.anki("notesInfo", notes=ids[i : i + 200]):
            if not n or n.get("modelName") != NOTE_TYPE:
                continue
            value = n["fields"].get(DEF_FIELD, {}).get("value", "")
            if not re.search(r"<li\b", value, re.I):
                continue  # no list, nothing to do
            new = to_lines(value)
            word = re.sub(
                r"<[^>]+>", "", n["fields"].get("wordAsWritten", {}).get("value", "")
            )
            if new is None:
                odd.append(f"{n['noteId']} {word}: {value[:120]!r}")
                continue
            converted += 1
            if MODE == "dry-run":
                if shown < 15:
                    print(f"  {word}: {new.replace(JOINER, ' | ')}")
                    shown += 1
                continue
            log.write(
                f"{n['noteId']}\t{json.dumps(value, ensure_ascii=False)}\t"
                f"{json.dumps(new, ensure_ascii=False)}\n"
            )
            log.flush()
            crop.anki(
                "updateNoteFields", note={"id": n["noteId"], "fields": {DEF_FIELD: new}}
            )
            time.sleep(0.02)
    if log:
        log.close()
    print(
        f"\n{converted} definitions {'to convert' if MODE == 'dry-run' else 'converted'}"
    )
    if odd:
        print(f"{len(odd)} have a list in another shape and are left alone, e.g.:")
        print("\n".join("  " + o for o in odd[:10]))
    if MODE == "dry-run":
        print('\nDRY RUN - set MODE = "convert" to write.')
    else:
        print(f'Log: {LOG_FILE}. To undo: MODE = "revert".')


if __name__ == "__main__":
    main()
