"""Browser: a search for one word lists that word's own card first.

Typing 共に shows the 共に card first, then cards whose word contains it (と共に),
then everything else that matched (sentences that contain 共に). Each group keeps
the order of the column you sort by. Works next to filters too (tag:free_card 助):
it needs exactly one plain word in the search; wildcards and phrases are left alone.
"""
import re

from aqt import gui_hooks

WORD_FIELD = "word"
EXACT_FIELDS = ("word", "reading-plain", "word-as-written")
PLAIN = re.compile(r'^[^\s:"()*_\\\-][^\s:"()*_\\]*$')
TOKENS = re.compile(r'"(?:[^"\\]|\\.)*"|\S+')
OPERATORS = {"and", "or"}


def the_word(search):
    """the one plain word in a search, next to any filters (tag:x, deck:y, -z)"""
    words = [t for t in TOKENS.findall(search.replace("(", " ").replace(")", " "))
             if PLAIN.match(t) and t.lower() not in OPERATORS]
    return words[0] if len(words) == 1 else None


def first_the_word(ctx):
    try:
        term = the_word(ctx.search or "")
        if not ctx.ids or not term:
            return
        col = ctx.browser.col
        find = col.find_notes if ctx.browser.table.is_notes_mode() else col.find_cards
        exact = set(find(" OR ".join(f'"{f}:{term}"' for f in EXACT_FIELDS)))
        part = set(find(f'"{WORD_FIELD}:*{term}*"')) - exact
        if not exact and not part:
            return
        ids = list(ctx.ids)
        ctx.ids = ([i for i in ids if i in exact] + [i for i in ids if i in part]
                   + [i for i in ids if i not in exact and i not in part])
    except Exception as e:  # never break the browser over this
        print("word_first_search:", e)


gui_hooks.browser_did_search.append(first_the_word)
